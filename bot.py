from ytmusicapi import YTMusic
import time
import re


# ============================================================
# CONFIGURACIÓN
# ============================================================

ytmusic = YTMusic()


# ============================================================
# 35 ARTISTAS DEFINITIVOS
# ============================================================

ARTISTS = {
    "Bebeshito": "UCpVfWS-cPOE2sYqsFuuP_Qg",
    "Charly & Johayron": "UCnwEtOQyXJUUuBhcTgImdfQ",
    "Dany Ome": "UCJQEm9t4KjDn-I8Fahf4Uqw",
    "Wampi": "UCbfzw8u1lCwDMv443StJEOw",
    "El Taiger": "UCoYtt7bGCV5RyUweyQgqQ4A",
    "Ja Rulay": "UCcaU4COep7mj8kbXwS24JFQ",
    "L Kimii": "UCMyQosiL8iVUtXPIm1UZJQg",
    "El Dray": "UC4kpn8y8QXYXmyDn8HJKD8Q",
    "Mauro y El Pitu": "UCvN1mRFfAfWYTiIkM70qUWA",
    "Yirow Y El Tingo": "UCEq3_5h1Xi_vLbytP7OzuNA",
    "Nany La Kbra": "UCG4lSNdNx_LuLnN2EW6uWwQ",
    "Ya Ice Dilan": "UC9aJbR9Q8nscvZaMw_cH4Ww",
    "Rey Tony": "UCDhExL0uVtumv_DEjPPq5qg",
    "Baby Maikol": "UCP5R6Mgbk_bgtgzZguLNKdA",
    "Payaso X Ley": "UCauTaqBvFqqqJTu3B4Wc1GA",
    "Kaly Y Kowa": "UCSfR51myQhs2ZcdzrWo0Z4w",
    "Wildey": "UCmFS-VSa4Wf3F1wdWS-8p_g",
    "Wow Popy": "UCtFkN8UFxT_MuNdySlfuFuA",
    "Talent Fuego": "UC0dVmcXfNa7lVeUBve3_FXw",
    "Mawell": "UCL6P-jUDZEKBA-Lb6WFccWg",
    "Harryson": "UC2ihX5uoblnN4wsA-ayIAAA",
    "El Chulo": "UCiT8VNdnpeYnCTPJZoqym9g",
    "Fixty Ordara": "UCDHDCbVOQywsLCsCZ8PH-AA",
    "El Kamel": "UCPnWcazEV7QM0H7qBx6NVXg",
    "Velito el Bufón": "UCRA9cRfAJXuxDRcFnoB7pwg",
    "Un Titico": "UCT2KiGFSPZIF3DR9UIN2fYw",
    "Musteerifa": "UCiT8PzlQqtPC7lWFh3--4jw",
    "Chocolate MC": "UCYVuThmAmbXxk1o9Un5Cc_w",
    "El Chacal": "UCJt4IsSmUjqTaamhCJoKK_g",
    "El Micha": "UCHhrMSqe_C1E_JBEz3mRlew",
    "Yomil": "UCPfXwOpwRIbVsqqTsgt4i5g",
    "Jacob Forever": "UCJ1-Pwsroy-gzMqlfKDF4Hg",
    "Gente de Zona": "UCl2KQVc_GFH081i7b9CJQug",
    "La Diosa": "UChbVOQHgq01JoHY4axuWV0A",
    "Seidy La Niña": "UCFqYfgj_7h3ZUkBnyYS-TFg",
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalize(text):
    """
    Normaliza texto para poder comparar títulos.
    """
    if not text:
        return ""

    text = text.lower()

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

    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_title(item):
    """
    Obtiene el título de un resultado de YouTube Music.
    """
    if not isinstance(item, dict):
        return None

    return (
        item.get("title")
        or item.get("name")
    )


def get_item_type(item):
    """
    Intenta determinar si es álbum, sencillo, canción, etc.
    """
    if not isinstance(item, dict):
        return ""

    return (
        item.get("type")
        or item.get("resultType")
        or ""
    )


def get_year(item):
    """
    Obtiene el año si YouTube Music lo proporciona.
    """
    if not isinstance(item, dict):
        return ""

    return (
        item.get("year")
        or item.get("releaseYear")
        or ""
    )


def extract_results(data):
    """
    Convierte diferentes formatos de respuesta
    de ytmusicapi en una lista.
    """
    if not data:
        return []

    if isinstance(data, dict):
        data = data.get("results", [])

    if not isinstance(data, list):
        return []

    return data


# ============================================================
# OBTENER INFORMACIÓN DEL ARTISTA
# ============================================================

def get_artist_info(artist_name, channel_id):

    try:

        info = ytmusic.get_artist(channel_id)

        returned_name = (
            info.get("name")
            or info.get("artist")
            or info.get("title")
        )

        subscribers = (
            info.get("subscribers")
            or info.get("subscriberCount")
            or info.get("subscribersText")
            or "?"
        )

        return {
            "ok": True,
            "name": returned_name,
            "subscribers": subscribers,
            "info": info,
        }

    except Exception as e:

        return {
            "ok": False,
            "name": None,
            "subscribers": "?",
            "info": {},
            "error": str(e),
        }


# ============================================================
# OBTENER LANZAMIENTOS VISIBLES
# ============================================================

def get_visible_releases(info):

    releases = []

    # Primero intentamos utilizar los elementos
    # que ya vienen en get_artist().
    for key in [
        "albums",
        "singles",
    ]:

        items = extract_results(
            info.get(key)
        )

        for item in items:

            title = get_title(item)

            if not title:
                continue

            releases.append({
                "title": title,
                "type": get_item_type(item),
                "year": get_year(item),
                "raw": item,
            })

    return releases


# ============================================================
# MOSTRAR LANZAMIENTOS
# ============================================================

def print_releases(releases):

    if not releases:

        print(
            "  No se encontraron lanzamientos "
            "en la respuesta inicial."
        )

        return

    for release in releases:

        title = release["title"]
        year = release["year"]
        item_type = release["type"]

        extra = []

        if year:
            extra.append(str(year))

        if item_type:
            extra.append(str(item_type))

        if extra:
            print(
                "  - "
                + title
                + " ["
                + " | ".join(extra)
                + "]"
            )
        else:
            print(
                "  - "
                + title
            )


# ============================================================
# PROCESAR ARTISTA
# ============================================================

def process_artist(artist_name, channel_id):

    print()
    print("=" * 70)
    print(artist_name)
    print("=" * 70)

    result = get_artist_info(
        artist_name,
        channel_id
    )

    if not result["ok"]:

        print("ERROR AL CONSULTAR ARTISTA")
        print(result["error"])

        return {
            "artist": artist_name,
            "ok": False,
            "releases": [],
        }

    print(
        "Nombre YouTube Music:",
        result["name"]
    )

    print(
        "Seguidores:",
        result["subscribers"]
    )

    releases = get_visible_releases(
        result["info"]
    )

    print()
    print("Lanzamientos visibles:")

    print_releases(releases)

    return {
        "artist": artist_name,
        "ok": True,
        "releases": releases,
    }


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print("=" * 70)
    print("CUBATON MUSIC")
    print("PRUEBA DE DETECCIÓN DE LANZAMIENTOS")
    print("=" * 70)

    print()
    print(
        "Artistas configurados:",
        len(ARTISTS)
    )

    print(
        "Modo: SOLO LECTURA"
    )

    print(
        "Telegram: NO SE PUBLICARÁ NADA"
    )

    print()

    total_artists = 0
    successful_artists = 0
    failed_artists = 0
    total_releases = 0

    all_results = []

    for artist_name, channel_id in ARTISTS.items():

        total_artists += 1

        result = process_artist(
            artist_name,
            channel_id
        )

        all_results.append(result)

        if result["ok"]:
            successful_artists += 1
            total_releases += len(
                result["releases"]
            )
        else:
            failed_artists += 1

        # Pequeña pausa para no hacer
        # demasiadas consultas seguidas.
        time.sleep(1)

    print()
    print()
    print("=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)

    print(
        "Artistas configurados:",
        total_artists
    )

    print(
        "Consultas exitosas:",
        successful_artists
    )

    print(
        "Consultas con error:",
        failed_artists
    )

    print(
        "Lanzamientos encontrados:",
        total_releases
    )

    print()

    if successful_artists == 35:
        print(
            "OK: los 35 artistas fueron consultados correctamente."
        )
    else:
        print(
            "ATENCIÓN: algunos artistas tuvieron problemas."
        )

    print()
    print("=" * 70)
    print("FIN DE LA PRUEBA")
    print("=" * 70)


if __name__ == "__main__":
    main()
