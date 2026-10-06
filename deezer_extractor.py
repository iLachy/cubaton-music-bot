import sys
import json
import re
import requests


DEEZER_API = "https://api.deezer.com"
TIMEOUT = 20


def api_get(endpoint):
    """
    Realiza una petición GET a la API pública de Deezer.
    """
    url = f"{DEEZER_API}{endpoint}"

    response = requests.get(
        url,
        timeout=TIMEOUT,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict) and data.get("error"):
        error = data["error"]
        message = error.get("message", "Error desconocido de Deezer")
        raise RuntimeError(message)

    return data


def parse_deezer_url(url):
    """
    Detecta si la URL corresponde a un track o a un álbum.
    """
    url = url.strip()

    match = re.search(
        r"deezer\.com/(?:[a-z]{2}/)?(track|album)/(\d+)",
        url,
        re.IGNORECASE
    )

    if not match:
        raise ValueError(
            "La URL no parece ser un enlace válido de Deezer "
            "de tipo /track/ID o /album/ID."
        )

    resource_type = match.group(1).lower()
    resource_id = int(match.group(2))

    return resource_type, resource_id


def format_date(date_string):
    """
    Convierte YYYY-MM-DD a DD-MM-YYYY.
    """
    if not date_string:
        return None

    try:
        year, month, day = date_string.split("-")
        return f"{day}-{month}-{year}"
    except Exception:
        return date_string


def format_duration(seconds):
    """
    Convierte segundos a MM:SS.
    """
    if seconds is None:
        return None

    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return None

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    return f"{minutes:02d}:{remaining_seconds:02d}"


def build_publication_title(title_short, title_version=None):
    """
    Construye el título que utilizaremos como título oficial
    dentro de nuestro sistema.

    Ejemplo:

        title_short  = "Le Metí"
        title_version = "(Prod. by El Bandolero)"

    Resultado:

        "Le Metí (Prod. by El Bandolero)"

    Si no existe title_version, se utiliza solamente title_short.
    """

    title_short = str(title_short or "").strip()
    title_version = str(title_version or "").strip()

    if not title_short:
        return title_version or ""

    if not title_version:
        return title_short

    # Evitar duplicar la versión si Deezer ya la incluye
    # dentro del título corto.
    if title_version.lower() in title_short.lower():
        return title_short

    # Evitar duplicar el título completo.
    if title_short.lower() in title_version.lower():
        return title_version

    return f"{title_short} {title_version}".strip()


def get_artists(data):
    """
    Obtiene todos los artistas principales desde contributors.

    Deezer puede colocar solamente al artista principal en el campo
    'artist', mientras que 'contributors' contiene las colaboraciones.
    """

    contributors = data.get("contributors") or []

    artists = []

    for contributor in contributors:
        role = str(contributor.get("role", "")).lower()

        # Solo consideramos artistas principales.
        if role and role != "main":
            continue

        name = contributor.get("name")

        if name and name not in artists:
            artists.append(name)

    # Fallback por si contributors no existe.
    if not artists:
        artist = data.get("artist") or {}

        name = artist.get("name")

        if name:
            artists.append(name)

    return ", ".join(artists)


def get_cover(data):
    """
    Obtiene la mejor portada disponible.
    """

    possible_covers = [
        data.get("cover_xl"),
        data.get("cover_big"),
        data.get("cover_medium"),
        data.get("cover"),
    ]

    for cover in possible_covers:
        if cover:
            return cover

    album = data.get("album") or {}

    possible_album_covers = [
        album.get("cover_xl"),
        album.get("cover_big"),
        album.get("cover_medium"),
        album.get("cover"),
    ]

    for cover in possible_album_covers:
        if cover:
            return cover

    return None


def get_release_type(album_data):
    """
    Obtiene el tipo interno de publicación de Deezer.
    """

    record_type = str(
        album_data.get("record_type") or ""
    ).lower()

    if record_type in ("single", "ep", "album"):
        return record_type

    # Fallback usando la cantidad de tracks.
    nb_tracks = album_data.get("nb_tracks")

    try:
        nb_tracks = int(nb_tracks)
    except (TypeError, ValueError):
        nb_tracks = None

    if nb_tracks == 1:
        return "single"

    return "album"


def get_publication_name(album_data, release_type):
    """
    Determina qué debe aparecer en:

        📀 Nombre de la publicación

    Reglas:

        Single -> "Single"
        EP     -> nombre real del EP
        Álbum  -> nombre real del álbum
    """

    if release_type == "single":
        return "Single"

    publication_title = album_data.get("title")

    if publication_title:
        return publication_title

    return "EP" if release_type == "ep" else "Álbum"


def get_track_title_data(track):
    """
    Obtiene el título limpio y el título editorial completo.

    Deezer proporciona normalmente:

        title_short
        title_version

    Nosotros conservamos ambos conceptos:

        titulo
        titulo_publicacion
    """

    titulo = (
        track.get("title_short")
        or track.get("title")
        or ""
    )

    title_version = (
        track.get("title_version")
        or ""
    )

    titulo_publicacion = build_publication_title(
        titulo,
        title_version
    )

    return titulo, titulo_publicacion


def build_track_data(track, album_data=None, deezer_url=None):
    """
    Convierte la información de un track de Deezer al formato
    utilizado por nuestro sistema.
    """

    if album_data is None:
        album_data = track.get("album") or {}

    track_id = track.get("id")

    album_id = album_data.get("id")

    # Artistas: preferimos contributors del track.
    artistas = get_artists(track)

    # Fallback a contributors del álbum.
    if not artistas and album_data:
        artistas = get_artists(album_data)

    # Título limpio + título editorial completo.
    titulo, titulo_publicacion = get_track_title_data(track)

    fecha_original = (
        track.get("release_date")
        or album_data.get("release_date")
    )

    fecha = format_date(fecha_original)

    duracion = format_duration(
        track.get("duration")
    )

    isrc = track.get("isrc")

    preview = track.get("preview")

    release_type = get_release_type(album_data)

    nombre_publicacion = get_publication_name(
        album_data,
        release_type
    )

    # Para un single queremos conservar la URL proporcionada
    # por el usuario. Para un track individual, si no existe,
    # construimos su URL.
    if deezer_url:
        final_deezer_url = deezer_url
    elif track_id:
        final_deezer_url = f"https://www.deezer.com/track/{track_id}"
    elif album_id:
        final_deezer_url = f"https://www.deezer.com/album/{album_id}"
    else:
        final_deezer_url = None

    result = {
        "artistas": artistas,
        "titulo": titulo,
        "titulo_publicacion": titulo_publicacion,
        "nombre_publicacion": nombre_publicacion,
        "duracion": duracion,
        "fecha": fecha,
        "portada": get_cover(track) or get_cover(album_data),
        "isrc": isrc,
        "preview_deezer": preview,
        "deezer_url": final_deezer_url,
        "deezer_track_id": track_id,
        "deezer_album_id": album_id,
    }

    return result


def extract_track(track_id, deezer_url=None):
    """
    Extrae información completa de un track.
    """

    track = api_get(f"/track/{track_id}")

    album = track.get("album") or {}

    # El endpoint del track contiene el álbum de forma resumida.
    # Si tenemos ID, consultamos el álbum completo para obtener
    # contributors, record_type, nb_tracks, etc.
    album_id = album.get("id")

    if album_id:
        try:
            album_full = api_get(f"/album/{album_id}")
        except Exception:
            album_full = album
    else:
        album_full = album

    return build_track_data(
        track,
        album_full,
        deezer_url=deezer_url
    )


def extract_album(album_id, deezer_url=None):
    """
    Extrae información de un álbum, EP o single.
    """

    album = api_get(f"/album/{album_id}")

    tracks_container = album.get("tracks") or {}
    tracks = tracks_container.get("data") or []

    release_type = get_release_type(album)

    # ---------------------------------------------------------
    # SINGLE
    # ---------------------------------------------------------
    #
    # Si el lanzamiento tiene un solo track, consultamos el
    # endpoint completo del track para obtener:
    #
    # - ISRC
    # - preview
    # - contributors
    # - duración exacta
    # - title_version
    #
    if release_type == "single" and len(tracks) >= 1:

        track_id = tracks[0].get("id")

        if track_id:
            return extract_track(
                track_id,
                deezer_url=deezer_url
            )

    # ---------------------------------------------------------
    # EP / ÁLBUM
    # ---------------------------------------------------------
    #
    # Para publicaciones con varios tracks conservamos la
    # información de cada canción.
    #

    nombre_publicacion = get_publication_name(
        album,
        release_type
    )

    album_artists = get_artists(album)

    fecha = format_date(
        album.get("release_date")
    )

    portada = get_cover(album)

    formatted_tracks = []

    for track_summary in tracks:

        track_id = track_summary.get("id")

        full_track = None

        if track_id:
            try:
                full_track = api_get(
                    f"/track/{track_id}"
                )
            except Exception:
                full_track = None

        if full_track:
            track = full_track
        else:
            track = track_summary

        artistas = get_artists(track)

        if not artistas:
            artistas = album_artists

        titulo, titulo_publicacion = get_track_title_data(
            track
        )

        track_fecha = format_date(
            track.get("release_date")
            or album.get("release_date")
        )

        formatted_tracks.append({
            "artistas": artistas,
            "titulo": titulo,
            "titulo_publicacion": titulo_publicacion,
            "nombre_publicacion": nombre_publicacion,
            "duracion": format_duration(
                track.get("duration")
            ),
            "fecha": track_fecha,
            "portada": get_cover(track) or portada,
            "isrc": track.get("isrc"),
            "preview_deezer": track.get("preview"),
            "deezer_track_id": track.get("id"),
            "deezer_album_id": album_id,
        })

    # Duración del álbum/EP no se utiliza como duración de una
    # canción. Se mantiene None a nivel de publicación.
    result = {
        "artistas": album_artists,
        "titulo": album.get("title") or "",
        "titulo_publicacion": album.get("title") or "",
        "nombre_publicacion": nombre_publicacion,
        "duracion": None,
        "fecha": fecha,
        "portada": portada,
        "isrc": None,
        "preview_deezer": None,
        "deezer_url": deezer_url
        or f"https://www.deezer.com/album/{album_id}",
        "deezer_track_id": None,
        "deezer_album_id": album_id,
        "tracks": formatted_tracks,
    }

    return result


def extract_deezer(url):
    """
    Punto principal del extractor.
    """

    resource_type, resource_id = parse_deezer_url(url)

    if resource_type == "track":
        return extract_track(
            resource_id,
            deezer_url=url
        )

    if resource_type == "album":
        return extract_album(
            resource_id,
            deezer_url=url
        )

    raise ValueError(
        "Tipo de recurso Deezer no soportado."
    )


def main():
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        "Debes proporcionar una URL de Deezer."
                    )
                },
                ensure_ascii=False,
                indent=2
            )
        )
        sys.exit(1)

    url = sys.argv[1]

    try:
        data = extract_deezer(url)

        print(
            json.dumps(
                {
                    "ok": True,
                    "data": data
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