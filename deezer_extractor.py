#!/usr/bin/env python3

import json
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests


DEEZER_API = "https://api.deezer.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class DeezerExtractorError(Exception):
    """Error controlado del extractor de Deezer."""


def api_get(endpoint: str) -> Dict[str, Any]:
    """Realiza una petición GET a la API pública de Deezer."""

    url = f"{DEEZER_API}/{endpoint.lstrip('/')}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )
    except requests.RequestException as exc:
        raise DeezerExtractorError(
            f"No se pudo conectar con Deezer: {exc}"
        ) from exc

    if response.status_code != 200:
        raise DeezerExtractorError(
            f"Deezer respondió HTTP {response.status_code}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise DeezerExtractorError(
            "Deezer no devolvió una respuesta JSON válida."
        ) from exc

    if isinstance(data, dict) and data.get("error"):
        error = data["error"]

        if isinstance(error, dict):
            message = error.get(
                "message",
                "Error desconocido",
            )
        else:
            message = str(error)

        raise DeezerExtractorError(
            f"Error de la API de Deezer: {message}"
        )

    return data


def extract_deezer_id(url: str) -> tuple[str, int]:
    """
    Extrae el tipo de recurso y su ID.

    Soporta:

        https://www.deezer.com/track/123456789
        https://www.deezer.com/album/123456789
    """

    url = url.strip()

    parsed = urlparse(url)

    hostname = parsed.netloc.lower()

    if hostname not in {
        "deezer.com",
        "www.deezer.com",
    }:
        raise DeezerExtractorError(
            "La URL no pertenece a Deezer."
        )

    match = re.search(
        r"/(track|album)/(\d+)",
        parsed.path,
        re.IGNORECASE,
    )

    if not match:
        raise DeezerExtractorError(
            "La URL debe ser de una pista o álbum de Deezer."
        )

    resource_type = match.group(1).lower()
    resource_id = int(match.group(2))

    return resource_type, resource_id


def format_date(
    date_value: Optional[str],
) -> Optional[str]:
    """Convierte YYYY-MM-DD a DD-MM-YYYY."""

    if not date_value:
        return None

    try:
        date_obj = datetime.strptime(
            date_value[:10],
            "%Y-%m-%d",
        )

        return date_obj.strftime("%d-%m-%Y")

    except ValueError:
        return date_value


def format_duration(
    seconds: Any,
) -> Optional[str]:
    """Convierte segundos a MM:SS."""

    if seconds is None:
        return None

    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return None

    if seconds < 0:
        return None

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    if hours > 0:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{remaining_seconds:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{remaining_seconds:02d}"
    )


def get_artists(
    data: Dict[str, Any],
) -> str:
    """
    Obtiene todos los artistas acreditados.

    Deezer proporciona los artistas colaboradores
    mediante el campo 'contributors'.
    """

    contributors = data.get("contributors")

    if not isinstance(contributors, list):
        return ""

    artists: List[str] = []

    for contributor in contributors:
        if not isinstance(contributor, dict):
            continue

        name = contributor.get("name")

        if not name:
            continue

        if name not in artists:
            artists.append(name)

    return ", ".join(artists)


def get_cover_url(
    album: Dict[str, Any],
) -> Optional[str]:
    """Obtiene la portada de mayor resolución disponible."""

    for key in (
        "cover_xl",
        "cover_big",
        "cover_medium",
        "cover",
    ):
        value = album.get(key)

        if value:
            return value

    return None


def normalize_record_type(
    record_type: Optional[str],
) -> str:
    """
    Convierte el tipo devuelto por Deezer
    a nuestro formato de publicación.
    """

    if not record_type:
        return "Álbum"

    normalized = record_type.strip().lower()

    mapping = {
        "single": "Single",
        "ep": "EP",
        "album": "Álbum",
    }

    return mapping.get(
        normalized,
        "Álbum",
    )


def get_release_type(
    album: Dict[str, Any],
) -> str:
    """Obtiene el tipo oficial del lanzamiento."""

    return normalize_record_type(
        album.get("record_type")
    )


def get_track_artists(
    track: Dict[str, Any],
    album: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Obtiene los artistas de una pista.

    Prioridad:
        1. contributors de la pista
        2. contributors del álbum
        3. artista principal
    """

    artists = get_artists(track)

    if artists:
        return artists

    if album:
        artists = get_artists(album)

        if artists:
            return artists

    artist = track.get("artist")

    if isinstance(artist, dict):
        return artist.get("name", "")

    return ""


def extract_from_track(
    track_id: int,
) -> Dict[str, Any]:
    """Extrae información completa de una pista."""

    track = api_get(
        f"track/{track_id}"
    )

    album = track.get("album")

    if not isinstance(album, dict):
        album = {}

    release_date = (
        track.get("release_date")
        or album.get("release_date")
    )

    artists = get_track_artists(
        track,
        album,
    )

    title = (
        track.get("title_short")
        or track.get("title")
    )

    if not title:
        raise DeezerExtractorError(
            "No se pudo obtener el título de la pista."
        )

    result = {
        "artistas": artists,
        "titulo": title,
        "tipo": get_release_type(album),
        "fecha": format_date(release_date),
        "duracion": format_duration(
            track.get("duration")
        ),
        "portada": get_cover_url(album),
        "isrc": track.get("isrc"),
        "preview_deezer": track.get("preview"),
        "deezer_url": track.get(
            "link",
            f"https://www.deezer.com/track/{track_id}",
        ),
        "deezer_track_id": track.get(
            "id",
            track_id,
        ),
        "deezer_album_id": album.get(
            "id"
        ),
    }

    return result


def extract_from_album(
    album_id: int,
) -> Dict[str, Any]:
    """
    Extrae información de un lanzamiento
    utilizando una URL /album/.
    """

    album = api_get(
        f"album/{album_id}"
    )

    tracks_data = album.get("tracks")

    if not isinstance(tracks_data, dict):
        raise DeezerExtractorError(
            "El álbum no contiene información de sus pistas."
        )

    tracks = tracks_data.get("data")

    if not isinstance(tracks, list) or not tracks:
        raise DeezerExtractorError(
            "El álbum no contiene pistas."
        )

    # ---------------------------------------------------------
    # Caso single de una pista
    # ---------------------------------------------------------

    if len(tracks) == 1:

        track_id = tracks[0].get("id")

        if not track_id:
            raise DeezerExtractorError(
                "La pista del lanzamiento no tiene ID."
            )

        # Consultamos /track/{id} porque aquí obtenemos
        # ISRC, contributors y preview completos.
        result = extract_from_track(
            int(track_id)
        )

        # La URL original proporcionada por el usuario
        # se conserva como referencia del lanzamiento.
        result["deezer_url"] = album.get(
            "link",
            f"https://www.deezer.com/album/{album_id}",
        )

        return result

    # ---------------------------------------------------------
    # Caso EP / álbum con varias pistas
    # ---------------------------------------------------------

    artists = get_artists(album)

    if not artists:
        artist = album.get("artist")

        if isinstance(artist, dict):
            artists = artist.get(
                "name",
                "",
            )

    release_date = album.get(
        "release_date"
    )

    total_duration = album.get(
        "duration"
    )

    result = {
        "artistas": artists,
        "titulo": album.get(
            "title",
            "",
        ),
        "tipo": get_release_type(album),
        "fecha": format_date(
            release_date
        ),
        "duracion": format_duration(
            total_duration
        ),
        "portada": get_cover_url(album),
        "isrc": None,
        "preview_deezer": None,
        "deezer_url": album.get(
            "link",
            f"https://www.deezer.com/album/{album_id}",
        ),
        "deezer_track_id": None,
        "deezer_album_id": album_id,
        "tracks": [],
    }

    # Guardamos las pistas para poder procesarlas
    # posteriormente de forma individual.
    for track in tracks:

        if not isinstance(track, dict):
            continue

        result["tracks"].append(
            {
                "id": track.get("id"),
                "titulo": (
                    track.get("title_short")
                    or track.get("title")
                ),
                "duracion": format_duration(
                    track.get("duration")
                ),
                "preview_deezer": track.get(
                    "preview"
                ),
            }
        )

    return result


def extract_deezer(
    url: str,
) -> Dict[str, Any]:
    """Función principal del extractor."""

    resource_type, resource_id = (
        extract_deezer_id(url)
    )

    if resource_type == "track":
        return extract_from_track(
            resource_id
        )

    if resource_type == "album":
        return extract_from_album(
            resource_id
        )

    raise DeezerExtractorError(
        f"Tipo de recurso no soportado: "
        f"{resource_type}"
    )


def main() -> None:
    """Punto de entrada para GitHub Actions."""

    if len(sys.argv) != 2:

        print(
            "Uso:\n"
            "  python deezer_extractor.py "
            "\"https://www.deezer.com/track/123456789\""
        )

        sys.exit(1)

    url = sys.argv[1]

    try:

        result = extract_deezer(
            url
        )

    except DeezerExtractorError as exc:

        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        sys.exit(1)

    print(
        json.dumps(
            {
                "ok": True,
                "data": result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()