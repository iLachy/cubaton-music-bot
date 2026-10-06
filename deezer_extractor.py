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
    """
    Realiza una petición GET a la API pública de Deezer.
    """

    url = f"{DEEZER_API}/{endpoint.lstrip('/')}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
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
            message = error.get("message", "Error desconocido")
        else:
            message = str(error)

        raise DeezerExtractorError(
            f"Error de la API de Deezer: {message}"
        )

    return data


def extract_deezer_id(url: str) -> tuple[str, int]:
    """
    Extrae el tipo de recurso y su ID desde una URL de Deezer.

    Soporta:
        /track/123
        /album/123
    """

    url = url.strip()

    parsed = urlparse(url)

    if parsed.netloc.lower() not in {
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


def format_date(date_value: Optional[str]) -> Optional[str]:
    """
    Convierte YYYY-MM-DD a DD-MM-YYYY.
    """

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


def format_duration(seconds: Any) -> Optional[str]:
    """
    Convierte segundos a MM:SS.
    """

    if seconds is None:
        return None

    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return None

    if seconds < 0:
        return None

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    return f"{minutes:02d}:{remaining_seconds:02d}"


def get_artist_names(track: Dict[str, Any]) -> str:
    """
    Obtiene los artistas de una pista.

    Prioridad:
        1. contributors
        2. artist principal
    """

    names: List[str] = []

    contributors = track.get("contributors")

    if isinstance(contributors, list):
        for contributor in contributors:
            if not isinstance(contributor, dict):
                continue

            name = contributor.get("name")

            if name and name not in names:
                names.append(name)

    artist = track.get("artist")

    if isinstance(artist, dict):
        artist_name = artist.get("name")

        if artist_name and artist_name not in names:
            names.insert(0, artist_name)

    if names:
        return ", ".join(names)

    return ""


def get_cover_url(album: Dict[str, Any]) -> Optional[str]:
    """
    Obtiene la portada en la mayor resolución disponible.
    """

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


def get_release_type(album: Dict[str, Any]) -> str:
    """
    Determina el tipo de publicación.

    La API puede devolver 'record_type' en algunos contextos.
    """

    record_type = album.get("record_type")

    if isinstance(record_type, str):
        normalized = record_type.strip().lower()

        if normalized in {
            "single",
            "ep",
            "album",
        }:
            return normalized.capitalize()

    album_type = album.get("type")

    if isinstance(album_type, str):
        normalized = album_type.strip().lower()

        if normalized in {
            "single",
            "ep",
            "album",
        }:
            return normalized.capitalize()

    return "Álbum"


def get_track_from_album(
    album: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Obtiene la pista principal de un lanzamiento.

    Para un álbum de varias pistas, por ahora no se selecciona
    arbitrariamente una pista como si fuera el lanzamiento.
    """

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

    if len(tracks) > 1:
        raise DeezerExtractorError(
            "La URL corresponde a un álbum/EP con varias pistas. "
            "En esta primera versión necesitamos decidir cómo "
            "procesar lanzamientos de varias pistas."
        )

    track = tracks[0]

    if not isinstance(track, dict):
        raise DeezerExtractorError(
            "La información de la pista no es válida."
        )

    return track


def extract_from_track(track_id: int) -> Dict[str, Any]:
    """
    Extrae información completa de una pista.
    """

    track = api_get(f"track/{track_id}")

    album = track.get("album")

    if not isinstance(album, dict):
        album = {}

    release_date = (
        track.get("release_date")
        or album.get("release_date")
    )

    artists = get_artist_names(track)

    title = track.get("title")

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
        "deezer_url": track.get(
            "link",
            f"https://www.deezer.com/track/{track_id}",
        ),
    }

    return result


def extract_from_album(album_id: int) -> Dict[str, Any]:
    """
    Extrae información de un lanzamiento usando una URL de álbum.
    """

    album = api_get(f"album/{album_id}")

    track = get_track_from_album(album)

    release_date = (
        album.get("release_date")
        or track.get("release_date")
    )

    artists = get_artist_names(track)

    if not artists:
        artist = album.get("artist")

        if isinstance(artist, dict):
            artists = artist.get("name", "")

    title = track.get("title")

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
        "deezer_url": album.get(
            "link",
            f"https://www.deezer.com/album/{album_id}",
        ),
    }

    return result


def extract_deezer(url: str) -> Dict[str, Any]:
    """
    Función principal.

    Acepta una URL de Deezer /track/ o /album/.
    """

    resource_type, resource_id = extract_deezer_id(url)

    if resource_type == "track":
        return extract_from_track(resource_id)

    if resource_type == "album":
        return extract_from_album(resource_id)

    raise DeezerExtractorError(
        f"Tipo de recurso no soportado: {resource_type}"
    )


def main() -> None:
    """
    Permite ejecutar el extractor desde la terminal.

    Uso:

        python deezer_extractor.py URL
    """

    if len(sys.argv) != 2:
        print(
            "Uso:\n"
            "  python deezer_extractor.py "
            "\"https://www.deezer.com/track/123456789\""
        )

        sys.exit(1)

    url = sys.argv[1]

    try:
        result = extract_deezer(url)

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