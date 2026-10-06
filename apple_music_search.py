#!/usr/bin/env python3

import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from urllib.parse import quote

import requests


# ============================================================
# CONFIGURACIÓN
# ============================================================

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

DEFAULT_COUNTRY = "us"

SEARCH_LIMIT = 25

MATCH_THRESHOLD = 0.70

TITLE_WEIGHT = 0.50
ARTIST_WEIGHT = 0.35
DURATION_WEIGHT = 0.15


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalize_text(value):
    if value is None:
        return ""

    value = str(value)

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    value = value.casefold()

    value = value.replace(
        "&",
        " and "
    )

    value = re.sub(
        r"[^\w\s]",
        " ",
        value,
        flags=re.UNICODE
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value


# ============================================================
# VERSIONES
# ============================================================

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


def extract_versions(title):
    if not title:
        return set()

    text = str(title)

    found = set()

    groups = re.findall(
        r"\(([^()]*)\)",
        text
    )

    groups += re.findall(
        r"\[([^\[\]]*)\]",
        text
    )

    for group in groups:
        normalized = normalize_text(group)

        if not normalized:
            continue

        if normalized in VERSION_LABELS:
            found.add(normalized)
            continue

        for label in VERSION_LABELS:
            if label in normalized:
                found.add(label)

    return found


def version_compatibility(
    source_title,
    candidate_title
):
    source_versions = extract_versions(
        source_title
    )

    candidate_versions = extract_versions(
        candidate_title
    )

    if (
        not source_versions
        and not candidate_versions
    ):
        return (
            True,
            source_versions,
            candidate_versions,
            "Ambas versiones son normales."
        )

    if (
        source_versions
        and not candidate_versions
    ):
        return (
            False,
            source_versions,
            candidate_versions,
            "Apple Music no especifica la versión."
        )

    if (
        not source_versions
        and candidate_versions
    ):
        return (
            False,
            source_versions,
            candidate_versions,
            "Apple Music especifica una versión que Deezer no especifica."
        )

    if source_versions == candidate_versions:
        return (
            True,
            source_versions,
            candidate_versions,
            "Las versiones coinciden."
        )

    return (
        False,
        source_versions,
        candidate_versions,
        "Las versiones son diferentes."
    )


# ============================================================
# TÍTULO
# ============================================================

def title_similarity(
    source_title,
    candidate_title
):
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

    source_raw = str(
        source_title
    ).casefold().strip()

    candidate_raw = str(
        candidate_title
    ).casefold().strip()

    if (
        candidate_raw.startswith(
            source_raw + " "
        )
        or candidate_raw.startswith(
            source_raw + "("
        )
    ):
        return 0.95

    if (
        source_raw.startswith(
            candidate_raw + " "
        )
        or source_raw.startswith(
            candidate_raw + "("
        )
    ):
        return 0.95

    return SequenceMatcher(
        None,
        source,
        candidate
    ).ratio()


# ============================================================
# ARTISTAS
# ============================================================

def split_artists(value):
    if value is None:
        return []

    if isinstance(
        value,
        list
    ):
        result = []

        for artist in value:
            artist = str(
                artist
            ).strip()

            if artist:
                result.append(
                    artist
                )

        return result

    value = str(
        value
    )

    separators = [
        ",",
        " & ",
        " feat. ",
        " feat ",
        " ft. ",
        " ft ",
    ]

    result = [
        value
    ]

    for separator in separators:
        new_result = []

        for item in result:
            new_result.extend(
                item.split(
                    separator
                )
            )

        result = new_result

    return [
        item.strip()
        for item in result
        if item.strip()
    ]


def artist_similarity(
    source_artists,
    candidate_artist_name
):
    source = [
        normalize_text(
            artist
        )
        for artist in split_artists(
            source_artists
        )
        if normalize_text(
            artist
        )
    ]

    candidate = [
        normalize_text(
            artist
        )
        for artist in split_artists(
            candidate_artist_name
        )
        if normalize_text(
            artist
        )
    ]

    if not source or not candidate:
        return 0.0

    exact_matches = 0

    for source_artist in source:
        if source_artist in candidate:
            exact_matches += 1
            continue

        best_similarity = 0.0

        for candidate_artist in candidate:
            similarity = SequenceMatcher(
                None,
                source_artist,
                candidate_artist
            ).ratio()

            if similarity > best_similarity:
                best_similarity = similarity

        if best_similarity >= 0.90:
            exact_matches += 1

    return min(
        exact_matches / len(source),
        1.0
    )


# ============================================================
# DURACIÓN
# ============================================================

def duration_similarity(
    source_duration,
    candidate_duration
):
    if (
        source_duration is None
        or candidate_duration is None
    ):
        return 0.0

    try:
        source_duration = float(
            source_duration
        )

        candidate_duration = float(
            candidate_duration
        )
    except (
        TypeError,
        ValueError
    ):
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
# ISRC
# ============================================================

def normalize_isrc(value):
    if not value:
        return ""

    return re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value)
    ).upper()


# ============================================================
# PUNTUACIÓN
# ============================================================

def calculate_score(
    title_score,
    artist_score,
    duration_score,
    isrc_match
):
    score = (
        title_score * TITLE_WEIGHT
        + artist_score * ARTIST_WEIGHT
        + duration_score * DURATION_WEIGHT
    )

    # El ISRC es una señal extremadamente fuerte.
    if isrc_match:
        score = max(
            score,
            0.99
        )

    return round(
        score,
        4
    )


# ============================================================
# BÚSQUEDA EN APPLE
# ============================================================

def search_apple_music(
    title,
    artists,
    isrc="",
    duration_seconds=None,
    country=DEFAULT_COUNTRY
):
    queries = []

    title = (
        str(title)
        .strip()
        if title
        else ""
    )

    artists_list = split_artists(
        artists
    )

    if not title:
        raise ValueError(
            "Falta el título."
        )

    if artists_list:
        queries.append(
            f"{title} {artists_list[0]}"
        )

        queries.append(
            f"{title} {' '.join(artists_list)}"
        )

    queries.append(
        title
    )

    candidates = {}

    errors = []

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; MusicReleaseMonitor/1.0)"
        )
    })

    for query in queries:
        params = {
            "term": query,
            "country": country,
            "media": "music",
            "entity": "song",
            "limit": SEARCH_LIMIT,
            "explicit": "Yes",
        }

        try:
            response = session.get(
                ITUNES_SEARCH_URL,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            payload = response.json()

        except Exception as exc:
            errors.append(
                {
                    "query": query,
                    "error": str(exc),
                }
            )

            continue

        for item in payload.get(
            "results",
            []
        ):
            track_id = str(
                item.get(
                    "trackId"
                )
                or ""
            )

            if not track_id:
                continue

            candidates[
                track_id
            ] = item

    processed = []

    source_isrc = normalize_isrc(
        isrc
    )

    for item in candidates.values():
        candidate_title = (
            item.get(
                "trackName"
            )
            or ""
        )

        candidate_artist = (
            item.get(
                "artistName"
            )
            or ""
        )

        candidate_isrc = normalize_isrc(
            item.get(
                "isrc"
            )
        )

        candidate_duration = item.get(
            "trackTimeMillis"
        )

        if candidate_duration is not None:
            try:
                candidate_duration = (
                    float(
                        candidate_duration
                    )
                    / 1000.0
                )
            except (
                TypeError,
                ValueError
            ):
                candidate_duration = None

        title_score = title_similarity(
            title,
            candidate_title
        )

        artist_score = artist_similarity(
            artists_list,
            candidate_artist
        )

        duration_score = duration_similarity(
            duration_seconds,
            candidate_duration
        )

        isrc_match = bool(
            source_isrc
            and candidate_isrc
            and source_isrc
            == candidate_isrc
        )

        (
            version_compatible,
            source_versions,
            candidate_versions,
            version_reason
        ) = version_compatibility(
            title,
            candidate_title
        )

        score = calculate_score(
            title_score,
            artist_score,
            duration_score,
            isrc_match
        )

        preview_url = ""

        previews = item.get(
            "previewUrl"
        )

        if previews:
            preview_url = str(
                previews
            )

        apple_url = (
            item.get(
                "trackViewUrl"
            )
            or ""
        )

        processed.append(
            {
                "track_id": track_id,
                "titulo": candidate_title,
                "artista": candidate_artist,
                "album": (
                    item.get(
                        "collectionName"
                    )
                    or ""
                ),
                "isrc": candidate_isrc,
                "duracion_segundos": (
                    round(
                        candidate_duration,
                        3
                    )
                    if candidate_duration
                    is not None
                    else None
                ),
                "preview_url": preview_url,
                "apple_music_url": apple_url,
                "artwork_url": (
                    item.get(
                        "artworkUrl100"
                    )
                    or ""
                ),
                "release_date": (
                    item.get(
                        "releaseDate"
                    )
                    or ""
                ),
                "explicit": (
                    item.get(
                        "trackExplicitness"
                    )
                    == "explicit"
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
                "isrc_match": isrc_match,
                "score": score,
                "version_compatible": (
                    version_compatible
                ),
                "source_versions": sorted(
                    source_versions
                ),
                "candidate_versions": sorted(
                    candidate_versions
                ),
                "version_reason": (
                    version_reason
                ),
            }
        )

    processed.sort(
        key=lambda item: (
            item[
                "version_compatible"
            ],
            item[
                "isrc_match"
            ],
            item[
                "score"
            ],
        ),
        reverse=True
    )

    valid_candidates = [
        item
        for item in processed
        if (
            item[
                "version_compatible"
            ]
            and item[
                "score"
            ] >= MATCH_THRESHOLD
        )
    ]

    best = (
        valid_candidates[0]
        if valid_candidates
        else None
    )

    result = {
        "ok": True,
        "data": {
            "encontrado": (
                best is not None
                and bool(
                    best.get(
                        "preview_url"
                    )
                )
            ),
            "titulo_apple": (
                best.get(
                    "titulo"
                )
                if best
                else ""
            ),
            "artista_apple": (
                best.get(
                    "artista"
                )
                if best
                else ""
            ),
            "album_apple": (
                best.get(
                    "album"
                )
                if best
                else ""
            ),
            "isrc_apple": (
                best.get(
                    "isrc"
                )
                if best
                else ""
            ),
            "apple_music_url": (
                best.get(
                    "apple_music_url"
                )
                if best
                else ""
            ),
            "preview_apple": (
                best.get(
                    "preview_url"
                )
                if best
                else ""
            ),
            "portada_apple": (
                best.get(
                    "artwork_url"
                )
                if best
                else ""
            ),
            "duracion_apple_segundos": (
                best.get(
                    "duracion_segundos"
                )
                if best
                else None
            ),
            "fecha_apple": (
                best.get(
                    "release_date"
                )
                if best
                else ""
            ),
            "explicito": (
                best.get(
                    "explicit"
                )
                if best
                else False
            ),
            "mejor_puntuacion": (
                best.get(
                    "score"
                )
                if best
                else 0.0
            ),
            "title_score": (
                best.get(
                    "title_score"
                )
                if best
                else 0.0
            ),
            "artist_score": (
                best.get(
                    "artist_score"
                )
                if best
                else 0.0
            ),
            "duration_score": (
                best.get(
                    "duration_score"
                )
                if best
                else 0.0
            ),
            "isrc_match": (
                best.get(
                    "isrc_match"
                )
                if best
                else False
            ),
            "version_compatible": (
                best.get(
                    "version_compatible"
                )
                if best
                else False
            ),
            "source_versions": (
                sorted(
                    best.get(
                        "source_versions",
                        []
                    )
                )
                if best
                else []
            ),
            "candidate_versions": (
                sorted(
                    best.get(
                        "candidate_versions",
                        []
                    )
                )
                if best
                else []
            ),
            "version_reason": (
                best.get(
                    "version_reason"
                )
                if best
                else ""
            ),
            "resultados": processed,
            "errores_busqueda": errors,
        }
    }

    return result


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 3:
        print(
            "Uso:"
        )
        print(
            "python apple_music_search.py "
            '"TITULO" '
            '"ARTISTAS" '
            '"ISRC" '
            '"DURACION_SEGUNDOS" '
            '[COUNTRY]'
        )
        sys.exit(1)

    title = sys.argv[1]

    artists = sys.argv[2]

    isrc = (
        sys.argv[3]
        if len(sys.argv) >= 4
        else ""
    )

    duration_seconds = None

    if (
        len(sys.argv) >= 5
        and sys.argv[4]
    ):
        try:
            duration_seconds = float(
                sys.argv[4]
            )
        except ValueError:
            duration_seconds = None

    country = (
        sys.argv[5].lower()
        if len(sys.argv) >= 6
        and sys.argv[5]
        else DEFAULT_COUNTRY
    )

    try:
        result = search_apple_music(
            title=title,
            artists=artists,
            isrc=isrc,
            duration_seconds=duration_seconds,
            country=country
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as exc:
        result = {
            "ok": False,
            "error": str(exc)
        }

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        sys.exit(1)


if __name__ == "__main__":
    main()