import sys
import json
import re
from difflib import SequenceMatcher

from ytmusicapi import YTMusic


SEARCH_LIMIT = 10

# Umbral mínimo para considerar que encontramos una coincidencia.
MATCH_THRESHOLD = 0.70


def normalize_text(text):
    """
    Normaliza texto para realizar comparaciones.

    No modifica el título que finalmente utilizaremos.
    Solamente crea una representación interna para el matching.
    """

    if not text:
        return ""

    text = str(text).lower()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9]+", " ", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text


def title_similarity(source_title, result_title):
    """
    Calcula la similitud entre el título oficial de nuestro
    sistema y el título devuelto por YouTube Music.

    Consideramos especialmente importante el caso en que
    YouTube Music añada información al final del título.

    Ejemplo:

        Le Metí
        Le Metí (Prod. by El Bandolero)

    Esto debe considerarse una coincidencia fuerte.
    """

    source = normalize_text(source_title)
    result = normalize_text(result_title)

    if not source or not result:
        return 0.0

    # Coincidencia exacta.
    if source == result:
        return 1.0

    # Si el resultado de YTM comienza exactamente con nuestro
    # título, consideramos que probablemente se trata de una
    # versión enriquecida del mismo título.
    if result.startswith(source + " "):
        return 0.95

    # También contemplamos directamente el caso de paréntesis.
    if result.startswith(source + "("):
        return 0.95

    # Comparación general como fallback.
    return SequenceMatcher(
        None,
        source,
        result
    ).ratio()


def get_result_artists(result):
    """
    Obtiene los nombres de los artistas de un resultado de YTM.
    """

    artists = result.get("artists") or []

    names = []

    for artist in artists:

        name = artist.get("name")

        if name and name not in names:
            names.append(name)

    return names


def artists_similarity(source_artists, result_artists):
    """
    Compara los artistas de Deezer con los artistas de YTM.

    No exigimos coincidencia exacta de cantidad porque una
    plataforma puede mostrar colaboradores de forma diferente.
    """

    if not source_artists or not result_artists:
        return 0.0

    normalized_source = [
        normalize_text(artist)
        for artist in source_artists
        if artist
    ]

    normalized_result = [
        normalize_text(artist)
        for artist in result_artists
        if artist
    ]

    if not normalized_source or not normalized_result:
        return 0.0

    matches = 0

    for source_artist in normalized_source:

        best_similarity = 0.0

        for result_artist in normalized_result:

            similarity = SequenceMatcher(
                None,
                source_artist,
                result_artist
            ).ratio()

            if similarity > best_similarity:
                best_similarity = similarity

        if best_similarity >= 0.80:
            matches += 1

    return matches / len(normalized_source)


def duration_similarity(
    source_duration_seconds,
    result_duration_seconds
):
    """
    Compara las duraciones.

    Una diferencia de pocos segundos es normal entre plataformas,
    por lo que no exigimos igualdad exacta.
    """

    if (
        source_duration_seconds is None
        or result_duration_seconds is None
    ):
        return 0.0

    try:
        source = int(source_duration_seconds)
        result = int(result_duration_seconds)
    except (TypeError, ValueError):
        return 0.0

    difference = abs(source - result)

    if difference == 0:
        return 1.0

    if difference <= 2:
        return 0.95

    if difference <= 5:
        return 0.85

    if difference <= 10:
        return 0.65

    if difference <= 20:
        return 0.35

    return 0.0


def calculate_score(
    source_title,
    source_artists,
    source_duration_seconds,
    result
):
    """
    Calcula la puntuación global de una coincidencia.

    Pesos:

        Título     50 %
        Artistas   35 %
        Duración   15 %
    """

    result_title = result.get("title") or ""

    result_artists = get_result_artists(result)

    result_duration = result.get(
        "duration_seconds"
    )

    title_score = title_similarity(
        source_title,
        result_title
    )

    artist_score = artists_similarity(
        source_artists,
        result_artists
    )

    duration_score = duration_similarity(
        source_duration_seconds,
        result_duration
    )

    score = (
        title_score * 0.50
        +
        artist_score * 0.35
        +
        duration_score * 0.15
    )

    return {
        "score": round(score, 4),
        "title_score": round(title_score, 4),
        "artist_score": round(artist_score, 4),
        "duration_score": round(duration_score, 4),
    }


def search_youtube_music(
    titulo_publicacion,
    artists,
    isrc=None,
    duration_seconds=None
):
    """
    Busca una canción en YouTube Music utilizando como fuente
    maestra los datos proporcionados por Deezer.

    IMPORTANTE:

    titulo_publicacion NO será reemplazado por el título que
    devuelva YTM.

    YTM solamente nos proporciona:

        - coincidencia
        - video_id
        - URL
        - disponibilidad
        - datos auxiliares
    """

    ytmusic = YTMusic()

    artists = [
        artist.strip()
        for artist in (artists or [])
        if artist and artist.strip()
    ]

    titulo_publicacion = (
        titulo_publicacion or ""
    ).strip()

    if not titulo_publicacion:
        raise ValueError(
            "titulo_publicacion es obligatorio."
        )

    if not artists:
        raise ValueError(
            "Debe existir al menos un artista."
        )

    # ---------------------------------------------------------
    # CONSULTAS
    # ---------------------------------------------------------

    queries = []

    # Consulta principal:
    # título editorial completo + todos los artistas.
    query_full = (
        f"{titulo_publicacion} "
        f"{' '.join(artists)}"
    )

    queries.append(query_full)

    # Consulta con título + artista principal.
    query_main_artist = (
        f"{titulo_publicacion} {artists[0]}"
    )

    if query_main_artist not in queries:
        queries.append(query_main_artist)

    # Como último recurso, solamente título.
    if titulo_publicacion not in queries:
        queries.append(titulo_publicacion)

    # ---------------------------------------------------------
    # BUSCAR
    # ---------------------------------------------------------

    candidates = {}

    search_errors = []

    for query in queries:

        try:

            results = ytmusic.search(
                query,
                filter="songs",
                limit=SEARCH_LIMIT,
                ignore_spelling=False
            )

        except Exception as e:

            search_errors.append({
                "query": query,
                "error": str(e)
            })

            continue

        for result in results:

            video_id = result.get("videoId")

            if not video_id:
                continue

            if video_id not in candidates:
                candidates[video_id] = result

    # ---------------------------------------------------------
    # RANKING
    # ---------------------------------------------------------

    ranked = []

    for result in candidates.values():

        scores = calculate_score(
            source_title=titulo_publicacion,
            source_artists=artists,
            source_duration_seconds=duration_seconds,
            result=result
        )

        ranked.append({
            "result": result,
            **scores
        })

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # ---------------------------------------------------------
    # SIN RESULTADOS
    # ---------------------------------------------------------

    if not ranked:

        return {
            "encontrado": False,

            "titulo_publicacion": titulo_publicacion,

            "artistas_buscados": artists,

            "isrc": isrc,

            "youtube_music_url": None,

            "video_id": None,

            "titulo_ytmusic": None,

            "artistas_ytmusic": [],

            "disponible": False,

            "mejor_puntuacion": 0,

            "title_score": 0,

            "artist_score": 0,

            "duration_score": 0,

            "resultados": [],

            "errores_busqueda": search_errors
        }

    # ---------------------------------------------------------
    # MEJOR RESULTADO
    # ---------------------------------------------------------

    best = ranked[0]

    result = best["result"]

    score = best["score"]

    video_id = result.get("videoId")

    youtube_music_url = None

    if video_id:

        youtube_music_url = (
            "https://music.youtube.com/watch?v="
            + video_id
        )

    result_artists = get_result_artists(result)

    # Un resultado solamente se considera encontrado si
    # supera nuestro umbral y está disponible.
    disponible = result.get("isAvailable")

    encontrado = (
        score >= MATCH_THRESHOLD
        and disponible is not False
    )

    # ---------------------------------------------------------
    # TOP RESULTADOS
    # ---------------------------------------------------------

    top_results = []

    for item in ranked[:5]:

        candidate = item["result"]

        candidate_video_id = candidate.get(
            "videoId"
        )

        candidate_url = None

        if candidate_video_id:

            candidate_url = (
                "https://music.youtube.com/watch?v="
                + candidate_video_id
            )

        top_results.append({
            "titulo": candidate.get("title"),

            "artistas": get_result_artists(
                candidate
            ),

            "duracion": candidate.get(
                "duration"
            ),

            "duracion_segundos": candidate.get(
                "duration_seconds"
            ),

            "video_id": candidate_video_id,

            "youtube_music_url": candidate_url,

            "disponible": candidate.get(
                "isAvailable"
            ),

            "explicito": candidate.get(
                "isExplicit"
            ),

            "score": item["score"],

            "title_score": item[
                "title_score"
            ],

            "artist_score": item[
                "artist_score"
            ],

            "duration_score": item[
                "duration_score"
            ]
        })

    # ---------------------------------------------------------
    # RESULTADO FINAL
    # ---------------------------------------------------------

    return {
        "encontrado": encontrado,

        # ESTE ES EL TÍTULO OFICIAL DE NUESTRO SISTEMA.
        "titulo_publicacion": titulo_publicacion,

        "artistas_buscados": artists,

        "isrc": isrc,

        # Información encontrada en YTM.
        # No sustituye nuestro titulo_publicacion.
        "titulo_ytmusic": result.get(
            "title"
        ),

        "artistas_ytmusic": result_artists,

        "youtube_music_url": youtube_music_url,

        "video_id": video_id,

        "duracion_ytmusic": result.get(
            "duration"
        ),

        "duracion_ytmusic_segundos": result.get(
            "duration_seconds"
        ),

        "disponible": disponible,

        "explicito": result.get(
            "isExplicit"
        ),

        "mejor_puntuacion": score,

        "title_score": best[
            "title_score"
        ],

        "artist_score": best[
            "artist_score"
        ],

        "duration_score": best[
            "duration_score"
        ],

        "resultados": top_results,

        "errores_busqueda": search_errors
    }


def main():

    if len(sys.argv) < 3:

        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        "Uso: "
                        "python youtube_music_search.py "
                        "\"TITULO_PUBLICACION\" "
                        "\"ARTISTA1, ARTISTA2\" "
                        "[ISRC] "
                        "[DURACION_SEGUNDOS]"
                    )
                },
                ensure_ascii=False,
                indent=2
            )
        )

        sys.exit(1)

    titulo_publicacion = sys.argv[1]

    artists = [
        artist.strip()
        for artist in sys.argv[2].split(",")
        if artist.strip()
    ]

    isrc = None

    if len(sys.argv) >= 4:

        isrc = (
            sys.argv[3].strip()
            or None
        )

    duration_seconds = None

    if len(sys.argv) >= 5:

        try:

            duration_seconds = int(
                sys.argv[4]
            )

        except (TypeError, ValueError):

            duration_seconds = None

    try:

        result = search_youtube_music(
            titulo_publicacion=titulo_publicacion,
            artists=artists,
            isrc=isrc,
            duration_seconds=duration_seconds
        )

        print(
            json.dumps(
                {
                    "ok": True,
                    "data": result
                },
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as e:

        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(e)
                },
                ensure_ascii=False,
                indent=2
            )
        )

        sys.exit(1)


if __name__ == "__main__":
    main()