import sys
import json
import re
from difflib import SequenceMatcher

from ytmusicapi import YTMusic


SEARCH_LIMIT = 10


def normalize_text(text):
    """
    Normaliza texto para facilitar las comparaciones.

    Ejemplo:
        "Le Metí (Prod. by El Bandolero)"
        ->
        "le meti prod by el bandolero"
    """

    if not text:
        return ""

    text = str(text).lower()

    # Eliminar acentos.
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

    # Sustituir cualquier cosa que no sea letra/número
    # por espacios.
    text = re.sub(r"[^a-z0-9]+", " ", text)

    # Eliminar espacios repetidos.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def title_similarity(source_title, result_title):
    """
    Calcula similitud entre dos títulos.
    """

    source = normalize_text(source_title)
    result = normalize_text(result_title)

    if not source or not result:
        return 0.0

    return SequenceMatcher(
        None,
        source,
        result
    ).ratio()


def get_result_artists(result):
    """
    Obtiene los nombres de los artistas de un resultado
    de YouTube Music.
    """

    artists = result.get("artists") or []

    names = []

    for artist in artists:
        name = artist.get("name")

        if name:
            names.append(name)

    return names


def artists_similarity(source_artists, result_artists):
    """
    Compara los artistas de Deezer con los artistas del
    resultado de YouTube Music.

    No exigimos que sean exactamente iguales porque
    YouTube Music puede mostrar solo parte de los
    colaboradores.
    """

    if not source_artists or not result_artists:
        return 0.0

    normalized_source = [
        normalize_text(x)
        for x in source_artists
        if x
    ]

    normalized_result = [
        normalize_text(x)
        for x in result_artists
        if x
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


def calculate_score(
    source_title,
    source_artists,
    result
):
    """
    Calcula una puntuación global para un resultado.
    """

    result_title = result.get("title") or ""

    result_artists = get_result_artists(result)

    title_score = title_similarity(
        source_title,
        result_title
    )

    artist_score = artists_similarity(
        source_artists,
        result_artists
    )

    # El título tiene mayor peso.
    score = (
        title_score * 0.65
        +
        artist_score * 0.35
    )

    return {
        "score": round(score, 4),
        "title_score": round(title_score, 4),
        "artist_score": round(artist_score, 4),
    }


def search_youtube_music(
    title,
    artists,
    isrc=None
):
    """
    Busca una canción en YouTube Music.

    Se realizan varias búsquedas:

    1. Título + artistas
    2. Título + artista principal
    3. Título

    El ISRC se conserva como dato de referencia, pero
    no se asume que YouTube Music lo permita buscar
    directamente.
    """

    ytmusic = YTMusic()

    artists = [
        artist.strip()
        for artist in (artists or [])
        if artist and artist.strip()
    ]

    title = (title or "").strip()

    if not title:
        raise ValueError(
            "El título de la canción es obligatorio."
        )

    if not artists:
        raise ValueError(
            "Debe existir al menos un artista."
        )

    queries = []

    # Búsqueda principal.
    query_full = f"{title} {' '.join(artists)}"

    queries.append(query_full)

    # Búsqueda con el artista principal.
    if len(artists) > 0:
        query_main = f"{title} {artists[0]}"

        if query_main not in queries:
            queries.append(query_main)

    # Búsqueda solamente por título.
    if title not in queries:
        queries.append(title)

    candidates = {}

    for query in queries:

        try:
            results = ytmusic.search(
                query,
                filter="songs",
                limit=SEARCH_LIMIT,
                ignore_spelling=False
            )

        except Exception as e:
            continue

        for result in results:

            video_id = result.get("videoId")

            if not video_id:
                continue

            if video_id not in candidates:
                candidates[video_id] = result

    ranked = []

    for result in candidates.values():

        scores = calculate_score(
            title,
            artists,
            result
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
            "titulo_buscado": title,
            "artistas_buscados": artists,
            "isrc": isrc,
            "youtube_music_url": None,
            "video_id": None,
            "mejor_puntuacion": 0,
            "resultados": []
        }

    # ---------------------------------------------------------
    # MEJOR RESULTADO
    # ---------------------------------------------------------

    best = ranked[0]

    result = best["result"]

    score = best["score"]

    # Umbral conservador.
    #
    # No queremos publicar automáticamente una canción
    # que tenga una coincidencia dudosa.
    encontrado = score >= 0.70

    video_id = result.get("videoId")

    youtube_music_url = None

    if video_id:
        youtube_music_url = (
            f"https://music.youtube.com/watch?v={video_id}"
        )

    artists_result = get_result_artists(result)

    # ---------------------------------------------------------
    # TOP RESULTADOS
    # ---------------------------------------------------------

    top_results = []

    for item in ranked[:5]:

        candidate = item["result"]

        candidate_video_id = candidate.get("videoId")

        candidate_url = None

        if candidate_video_id:
            candidate_url = (
                "https://music.youtube.com/watch?v="
                + candidate_video_id
            )

        top_results.append({
            "titulo": candidate.get("title"),
            "artistas": get_result_artists(candidate),
            "duracion": candidate.get("duration"),
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
            "title_score": item["title_score"],
            "artist_score": item["artist_score"],
        })

    return {
        "encontrado": encontrado,
        "titulo_buscado": title,
        "artistas_buscados": artists,
        "isrc": isrc,

        "titulo": result.get("title"),
        "artistas": artists_result,

        "youtube_music_url": youtube_music_url,
        "video_id": video_id,

        "duracion": result.get("duration"),
        "duracion_segundos": result.get(
            "duration_seconds"
        ),

        "disponible": result.get(
            "isAvailable"
        ),

        "explicito": result.get(
            "isExplicit"
        ),

        "mejor_puntuacion": score,
        "title_score": best["title_score"],
        "artist_score": best["artist_score"],

        "resultados": top_results
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
                        "\"TITULO\" "
                        "\"ARTISTA1, ARTISTA2\" "
                        "[ISRC]"
                    )
                },
                ensure_ascii=False,
                indent=2
            )
        )

        sys.exit(1)

    title = sys.argv[1]

    artists = [
        artist.strip()
        for artist in sys.argv[2].split(",")
        if artist.strip()
    ]

    isrc = None

    if len(sys.argv) >= 4:
        isrc = sys.argv[3].strip() or None

    try:

        result = search_youtube_music(
            title=title,
            artists=artists,
            isrc=isrc
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