import sys
import json
import re
import unicodedata
from difflib import SequenceMatcher

from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN
# ============================================================

MATCH_THRESHOLD = 0.70

TITLE_WEIGHT = 0.50
ARTIST_WEIGHT = 0.35
DURATION_WEIGHT = 0.15

MAX_RESULTS = 10

# ============================================================
# VARIANTES / VERSIONES MUSICALES
# ============================================================

# Estas etiquetas representan versiones que pueden cambiar
# sustancialmente la grabación.
#
# La comparación se hace de forma normalizada, por lo que:
#
# "Original Version"
# "original version"
# "ORIGINAL VERSION"
#
# se consideran iguales.

VERSION_LABELS = {
    "original",
    "original version",
    "original mix",
    "album version",
    "album mix",
    "radio edit",
    "radio version",
    "single version",
    "single edit",
    "remix",
    "remastered",
    "remaster",
    "instrumental",
    "acoustic",
    "live",
    "live version",
    "extended",
    "extended version",
    "extended mix",
    "edit",
    "version",
    "demo",
    "demo version",
    "club mix",
    "club version",
    "radio mix",
    "vocal mix",
    "dub mix",
    "dub version",
    "sped up",
    "slowed",
    "slowed + reverb",
    "slowed and reverb",
    "reverb",
    "nightcore",
}


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalize_text(text):
    """
    Normaliza texto para comparación:

    - convierte a minúsculas
    - elimina acentos
    - elimina espacios duplicados
    - conserva letras/números
    - convierte algunos separadores en espacios
    """

    if text is None:
        return ""

    text = str(text).strip().lower()

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    # Normalizar separadores frecuentes.
    text = text.replace(
        "–",
        "-"
    )

    text = text.replace(
        "—",
        "-"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# NORMALIZAR ARTISTA
# ============================================================

def normalize_artist(text):
    """
    Normalización específica para nombres de artistas.
    """

    return normalize_text(text)


# ============================================================
# EXTRAER CONTENIDO ENTRE PARÉNTESIS
# ============================================================

def extract_parenthetical_parts(title):
    """
    Extrae textos contenidos entre paréntesis.

    Ejemplo:

    "Levels (Original Version)"

    devuelve:

    ["Original Version"]
    """

    if not title:
        return []

    parts = re.findall(
        r"\(([^()]*)\)",
        str(title)
    )

    return [
        normalize_text(part)
        for part in parts
        if normalize_text(part)
    ]


# ============================================================
# EXTRAER CONTENIDO ENTRE CORCHETES
# ============================================================

def extract_bracket_parts(title):
    """
    Extrae textos contenidos entre corchetes.

    Ejemplo:

    "Song [Remix]"

    devuelve:

    ["Remix"]
    """

    if not title:
        return []

    parts = re.findall(
        r"\[([^\[\]]*)\]",
        str(title)
    )

    return [
        normalize_text(part)
        for part in parts
        if normalize_text(part)
    ]


# ============================================================
# DETECTAR ETIQUETAS DE VERSIÓN
# ============================================================

def extract_version_labels(title):
    """
    Extrae etiquetas relevantes de versión.

    Se consideran principalmente las expresiones dentro
    de paréntesis o corchetes.

    Ejemplo:

    "Levels (Original Version)"

    -> {"original version"}

    "Song (Remix)"

    -> {"remix"}
    """

    labels = set()

    parenthetical_parts = (
        extract_parenthetical_parts(title)
    )

    bracket_parts = (
        extract_bracket_parts(title)
    )

    all_parts = (
        parenthetical_parts
        + bracket_parts
    )

    for part in all_parts:

        normalized_part = normalize_text(
            part
        )

        if not normalized_part:
            continue

        # Coincidencia exacta.
        if normalized_part in VERSION_LABELS:

            labels.add(
                normalized_part
            )

            continue

        # Algunas etiquetas pueden aparecer
        # acompañadas de información adicional.
        #
        # Ejemplo:
        # "Remix by DJ X"
        #
        # En esos casos detectamos la etiqueta base.

        for label in VERSION_LABELS:

            pattern = (
                r"\b"
                + re.escape(label)
                + r"\b"
            )

            if re.search(
                pattern,
                normalized_part
            ):

                labels.add(
                    label
                )

    return labels


# ============================================================
# DETECTAR DIFERENCIA DE VERSIÓN
# ============================================================

def version_compatibility(
    source_title,
    candidate_title
):
    """
    Determina si la variante/version del resultado de
    YouTube Music es compatible con la de Deezer.

    Devuelve:

        {
            "compatible": True/False,
            "source_versions": [...],
            "candidate_versions": [...],
            "reason": "..."
        }

    Reglas:

    1. Si ninguno tiene etiqueta de versión:
       compatible.

    2. Si ambos tienen las mismas etiquetas:
       compatible.

    3. Si Deezer tiene una versión específica y YTM
       tiene otra diferente:
       incompatible.

    4. Si Deezer tiene una versión específica y YTM
       no indica ninguna versión:
       incompatible para las variantes consideradas
       críticas.

    Esto evita falsos positivos como:

        Levels (Original Version)
        ->
        Levels (Instrumental)
    """

    source_versions = extract_version_labels(
        source_title
    )

    candidate_versions = extract_version_labels(
        candidate_title
    )

    # --------------------------------------------------------
    # Ninguno especifica versión.
    # --------------------------------------------------------

    if not source_versions and not candidate_versions:

        return {
            "compatible": True,
            "source_versions": [],
            "candidate_versions": [],
            "reason": "Sin etiquetas de versión."
        }

    # --------------------------------------------------------
    # Ambos tienen exactamente la misma versión.
    # --------------------------------------------------------

    if source_versions == candidate_versions:

        return {
            "compatible": True,
            "source_versions": sorted(
                source_versions
            ),
            "candidate_versions": sorted(
                candidate_versions
            ),
            "reason": "Las etiquetas de versión coinciden."
        }

    # --------------------------------------------------------
    # Deezer tiene versión y YTM no.
    # --------------------------------------------------------

    if source_versions and not candidate_versions:

        return {
            "compatible": False,
            "source_versions": sorted(
                source_versions
            ),
            "candidate_versions": [],
            "reason": (
                "Deezer especifica una versión "
                "que YouTube Music no especifica."
            )
        }

    # --------------------------------------------------------
    # YTM tiene versión y Deezer no.
    # --------------------------------------------------------

    if not source_versions and candidate_versions:

        return {
            "compatible": False,
            "source_versions": [],
            "candidate_versions": sorted(
                candidate_versions
            ),
            "reason": (
                "YouTube Music especifica una versión "
                "que Deezer no especifica."
            )
        }

    # --------------------------------------------------------
    # Ambos tienen versiones diferentes.
    # --------------------------------------------------------

    return {
        "compatible": False,
        "source_versions": sorted(
            source_versions
        ),
        "candidate_versions": sorted(
            candidate_versions
        ),
        "reason": (
            "Las etiquetas de versión son diferentes."
        )
    }


# ============================================================
# COINCIDENCIA DE TÍTULO
# ============================================================

def title_similarity(
    source_title,
    candidate_title
):
    """
    Calcula similitud entre títulos.

    Se utiliza el título completo, incluyendo las variantes.

    Casos:

    "Le Metí (Prod. by El Bandolero)"
    ->
    mismo título
    ->
    1.0

    "Levels (Original Version)"
    ->
    "Levels (Instrumental)"
    ->
    similitud parcial
    """

    source = normalize_text(
        source_title
    )

    candidate = normalize_text(
        candidate_title
    )

    if not source or not candidate:
        return 0.0

    if source == candidate:
        return 1.0

    # --------------------------------------------------------
    # Coincidencia cuando YTM empieza con nuestro título.
    # --------------------------------------------------------

    if candidate.startswith(
        source + " "
    ):

        return 0.95

    if candidate.startswith(
        source + "("
    ):

        return 0.95

    # --------------------------------------------------------
    # Similaridad general.
    # --------------------------------------------------------

    return SequenceMatcher(
        None,
        source,
        candidate
    ).ratio()


# ============================================================
# COINCIDENCIA DE ARTISTAS
# ============================================================

def artist_similarity(
    source_artists,
    candidate_artists
):
    """
    Compara artistas.

    Para cada artista de Deezer busca la mejor coincidencia
    disponible entre los artistas de YouTube Music.

    Esto permite que YTM tenga menos créditos que Deezer.

    Ejemplo:

    Deezer:
        Bebeshito
        Dany Ome
        Kevincito El 13
        El Bandolero
        Roberto Ferrante

    YTM:
        Bebeshito
        Dany Ome
        Kevincito El 13
        El Bandolero

    El resultado puede seguir siendo aceptado.
    """

    if not source_artists:
        return 0.0

    if not candidate_artists:
        return 0.0

    source_normalized = [
        normalize_artist(
            artist
        )
        for artist in source_artists
        if normalize_artist(artist)
    ]

    candidate_normalized = [
        normalize_artist(
            artist
        )
        for artist in candidate_artists
        if normalize_artist(artist)
    ]

    if not source_normalized:
        return 0.0

    if not candidate_normalized:
        return 0.0

    scores = []

    for source_artist in source_normalized:

        best = 0.0

        for candidate_artist in candidate_normalized:

            if (
                source_artist
                == candidate_artist
            ):

                score = 1.0

            else:

                score = SequenceMatcher(
                    None,
                    source_artist,
                    candidate_artist
                ).ratio()

            if score > best:
                best = score

        scores.append(
            best
        )

    return sum(scores) / len(scores)


# ============================================================
# COINCIDENCIA DE DURACIÓN
# ============================================================

def duration_similarity(
    source_duration,
    candidate_duration
):
    """
    Compara duraciones en segundos.

    Reglas:

        exacta       -> 1.00
        <= 2 sec     -> 0.95
        <= 5 sec     -> 0.85
        <= 10 sec    -> 0.65
        <= 20 sec    -> 0.35
        > 20 sec     -> 0.00
    """

    if (
        source_duration is None
        or candidate_duration is None
    ):

        return 0.0

    try:

        source_duration = int(
            source_duration
        )

        candidate_duration = int(
            candidate_duration
        )

    except Exception:

        return 0.0

    difference = abs(
        source_duration
        - candidate_duration
    )

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


# ============================================================
# SCORE FINAL
# ============================================================

def calculate_score(
    title_score,
    artist_score,
    duration_score
):
    return (
        title_score * TITLE_WEIGHT
        +
        artist_score * ARTIST_WEIGHT
        +
        duration_score * DURATION_WEIGHT
    )


# ============================================================
# CONVERTIR ARTISTAS YTM
# ============================================================

def extract_ytmusic_artists(result):
    """
    Convierte la estructura de artistas de ytmusicapi
    a una lista simple de nombres.
    """

    artists = result.get(
        "artists"
    ) or []

    output = []

    for artist in artists:

        if isinstance(
            artist,
            dict
        ):

            name = artist.get(
                "name"
            )

        else:

            name = str(
                artist
            )

        if name:
            output.append(
                name
            )

    return output


# ============================================================
# PROCESAR RESULTADO YTM
# ============================================================

def process_result(
    result,
    source_title,
    source_artists,
    source_duration
):
    """
    Convierte un resultado bruto de ytmusicapi
    en nuestro formato interno.
    """

    candidate_title = (
        result.get(
            "title"
        )
        or ""
    )

    candidate_artists = (
        extract_ytmusic_artists(
            result
        )
    )

    candidate_duration = (
        result.get(
            "duration_seconds"
        )
    )

    title_score = title_similarity(
        source_title,
        candidate_title
    )

    artist_score = artist_similarity(
        source_artists,
        candidate_artists
    )

    duration_score = duration_similarity(
        source_duration,
        candidate_duration
    )

    score = calculate_score(
        title_score,
        artist_score,
        duration_score
    )

    # --------------------------------------------------------
    # Validación específica de versiones.
    # --------------------------------------------------------

    version_check = version_compatibility(
        source_title,
        candidate_title
    )

    # --------------------------------------------------------
    # Resultado procesado.
    # --------------------------------------------------------

    return {
        "titulo": candidate_title,

        "artistas": candidate_artists,

        "duracion": result.get(
            "duration"
        ),

        "duracion_segundos":
            candidate_duration,

        "video_id": result.get(
            "videoId"
        ),

        "youtube_music_url": (
            "https://music.youtube.com/watch?v="
            + str(
                result.get(
                    "videoId"
                )
            )
        )
        if result.get("videoId")
        else None,

        "disponible": result.get(
            "isAvailable",
            True
        ),

        "explicito": result.get(
            "isExplicit",
            False
        ),

        "score": round(
            score,
            4
        ),

        "title_score": round(
            title_score,
            4
        ),

        "artist_score": round(
            artist_score,
            4
        ),

        "duration_score": round(
            duration_score,
            4
        ),

        "version_compatible":
            version_check[
                "compatible"
            ],

        "source_versions":
            version_check[
                "source_versions"
            ],

        "candidate_versions":
            version_check[
                "candidate_versions"
            ],

        "version_reason":
            version_check[
                "reason"
            ],
    }


# ============================================================
# ARGUMENTOS
# ============================================================

def parse_arguments():

    if len(sys.argv) < 3:

        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        "Uso: "
                        "python youtube_music_search.py "
                        "\"titulo_publicacion\" "
                        "\"artistas\" "
                        "[isrc] "
                        "[duracion_segundos]"
                    )
                },
                ensure_ascii=False,
                indent=2
            )
        )

        sys.exit(1)

    titulo_publicacion = (
        sys.argv[1]
    )

    artists_string = (
        sys.argv[2]
    )

    isrc = (
        sys.argv[3]
        if len(sys.argv) >= 4
        else None
    )

    duration_seconds = None

    if len(sys.argv) >= 5:

        try:

            duration_seconds = int(
                sys.argv[4]
            )

        except Exception:

            duration_seconds = None

    artists = [
        artist.strip()
        for artist in artists_string.split(",")
        if artist.strip()
    ]

    return (
        titulo_publicacion,
        artists,
        isrc,
        duration_seconds
    )


# ============================================================
# BUSCAR
# ============================================================

def search_youtube_music(
    titulo_publicacion,
    artists,
    isrc=None,
    duration_seconds=None
):

    ytmusic = YTMusic()

    # --------------------------------------------------------
    # Construir consultas
    # --------------------------------------------------------

    queries = []

    all_artists = ", ".join(
        artists
    )

    if titulo_publicacion and all_artists:

        queries.append(
            f"{titulo_publicacion} {all_artists}"
        )

    if titulo_publicacion and artists:

        queries.append(
            f"{titulo_publicacion} {artists[0]}"
        )

    if titulo_publicacion:

        queries.append(
            titulo_publicacion
        )

    # Eliminar duplicados conservando orden.

    unique_queries = []

    for query in queries:

        if query not in unique_queries:

            unique_queries.append(
                query
            )

    # --------------------------------------------------------
    # Ejecutar búsquedas
    # --------------------------------------------------------

    raw_results = []

    errors = []

    for query in unique_queries:

        try:

            results = ytmusic.search(
                query,
                filter="songs",
                limit=MAX_RESULTS,
                ignore_spelling=False
            )

            raw_results.extend(
                results
            )

        except Exception as exc:

            errors.append(
                {
                    "query": query,
                    "error": str(exc)
                }
            )

    # --------------------------------------------------------
    # Eliminar resultados duplicados
    # --------------------------------------------------------

    unique_results = {}

    for result in raw_results:

        video_id = result.get(
            "videoId"
        )

        if not video_id:
            continue

        if video_id not in unique_results:

            unique_results[
                video_id
            ] = result

    # --------------------------------------------------------
    # Procesar candidatos
    # --------------------------------------------------------

    processed_results = []

    for result in unique_results.values():

        processed = process_result(
            result,
            titulo_publicacion,
            artists,
            duration_seconds
        )

        processed_results.append(
            processed
        )

    # --------------------------------------------------------
    # Ordenar por score
    # --------------------------------------------------------

    processed_results.sort(
        key=lambda item: (
            item["version_compatible"],
            item["score"]
        ),
        reverse=True
    )

    # --------------------------------------------------------
    # Buscar mejor candidato COMPATIBLE
    # --------------------------------------------------------

    compatible_results = [
        result
        for result in processed_results
        if result[
            "version_compatible"
        ]
    ]

    best_compatible = (
        compatible_results[0]
        if compatible_results
        else None
    )

    # --------------------------------------------------------
    # Comprobar disponibilidad y threshold
    # --------------------------------------------------------

    encontrado = False
    best_result = None

    if best_compatible:

        if (
            best_compatible["score"]
            >= MATCH_THRESHOLD
        ):

            if best_compatible[
                "disponible"
            ]:

                encontrado = True
                best_result = (
                    best_compatible
                )

    # --------------------------------------------------------
    # Construir resultados públicos
    # --------------------------------------------------------

    top_results = processed_results[
        :5
    ]

    # --------------------------------------------------------
    # Datos de salida
    # --------------------------------------------------------

    output = {

        "ok": True,

        "data": {

            # ----------------------------------------------
            # DATOS MAESTROS
            # ----------------------------------------------

            "encontrado":
                encontrado,

            "titulo_publicacion":
                titulo_publicacion,

            "artistas_buscados":
                artists,

            "isrc":
                isrc,

            # ----------------------------------------------
            # DATOS DEL MEJOR RESULTADO ACEPTADO
            # ----------------------------------------------

            "titulo_ytmusic":
                (
                    best_result["titulo"]
                    if best_result
                    else None
                ),

            "artistas_ytmusic":
                (
                    best_result["artistas"]
                    if best_result
                    else []
                ),

            "youtube_music_url":
                (
                    best_result[
                        "youtube_music_url"
                    ]
                    if best_result
                    else None
                ),

            "video_id":
                (
                    best_result[
                        "video_id"
                    ]
                    if best_result
                    else None
                ),

            "duracion_ytmusic":
                (
                    best_result[
                        "duracion"
                    ]
                    if best_result
                    else None
                ),

            "duracion_ytmusic_segundos":
                (
                    best_result[
                        "duracion_segundos"
                    ]
                    if best_result
                    else None
                ),

            "disponible":
                (
                    best_result[
                        "disponible"
                    ]
                    if best_result
                    else False
                ),

            "explicito":
                (
                    best_result[
                        "explicito"
                    ]
                    if best_result
                    else False
                ),

            "mejor_puntuacion":
                (
                    best_result[
                        "score"
                    ]
                    if best_result
                    else 0.0
                ),

            "title_score":
                (
                    best_result[
                        "title_score"
                    ]
                    if best_result
                    else 0.0
                ),

            "artist_score":
                (
                    best_result[
                        "artist_score"
                    ]
                    if best_result
                    else 0.0
                ),

            "duration_score":
                (
                    best_result[
                        "duration_score"
                    ]
                    if best_result
                    else 0.0
                ),

            # ----------------------------------------------
            # INFORMACIÓN DE VERSIÓN
            # ----------------------------------------------

            "version_compatible":
                (
                    best_result[
                        "version_compatible"
                    ]
                    if best_result
                    else False
                ),

            "source_versions":
                (
                    best_result[
                        "source_versions"
                    ]
                    if best_result
                    else sorted(
                        extract_version_labels(
                            titulo_publicacion
                        )
                    )
                ),

            "candidate_versions":
                (
                    best_result[
                        "candidate_versions"
                    ]
                    if best_result
                    else []
                ),

            "version_reason":
                (
                    best_result[
                        "version_reason"
                    ]
                    if best_result
                    else (
                        "No existe un candidato "
                        "compatible que supere "
                        "el umbral."
                    )
                ),

            # ----------------------------------------------
            # CANDIDATOS
            # ----------------------------------------------

            "resultados":
                top_results,

            # ----------------------------------------------
            # ERRORES
            # ----------------------------------------------

            "errores_busqueda":
                errors
        }
    }

    return output


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        (
            titulo_publicacion,
            artists,
            isrc,
            duration_seconds
        ) = parse_arguments()

        result = search_youtube_music(
            titulo_publicacion,
            artists,
            isrc,
            duration_seconds
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc)
                },
                ensure_ascii=False,
                indent=2
            )
        )

        sys.exit(1)


if __name__ == "__main__":
    main()