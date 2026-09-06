from ytmusicapi import YTMusic
import re
import time

ytmusic = YTMusic()

ARTISTS = {
    "Bebeshito": "UCpVfWS-cPOE2sYqsFuuP_Qg",
    "Charly & Johayron": "UCnwEtOQyXJUUuBhcTgImdfQ",
    "Dany Ome": "UCJQEm9t4KjDn-I8Fahf4Uqw",
    "Kevincito El 13": "UCDxpdRMANSbNf_Oy3FwBCRw",
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
    "Helabusador": "UC89ct8d1ZKEXS03nSpntgPg",
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


def normalize(text):
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
        "&": "and",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def names_match(expected, returned):
    if not returned:
        return False

    e = normalize(expected)
    r = normalize(returned)

    if e == r:
        return True

    if e in r or r in e:
        return True

    e_words = set(e.split())
    r_words = set(r.split())

    ignored = {
        "el",
        "la",
        "los",
        "las",
        "de",
        "y",
        "and",
        "mc",
        "official",
        "oficial",
        "music",
        "musica",
    }

    e_words -= ignored
    r_words -= ignored

    if e_words and r_words:
        return bool(e_words & r_words)

    return False


def get_subscribers(info):
    return (
        info.get("subscribers")
        or info.get("subscriberCount")
        or info.get("subscribersText")
        or "?"
    )


def extract_items(data):
    if not data:
        return []

    if isinstance(data, dict):
        data = data.get("results", [])

    if not isinstance(data, list):
        return []

    return data


def show_release(item):
    if not isinstance(item, dict):
        return None

    title = item.get("title") or item.get("name")

    if not title:
        return None

    year = (
        item.get("year")
        or item.get("releaseYear")
        or ""
    )

    item_type = (
        item.get("type")
        or item.get("resultType")
        or ""
    )

    if year:
        return f"{title} ({year})"

    if item_type:
        return f"{title} [{item_type}]"

    return title


def get_releases(info):
    releases = []

    for key in [
        "albums",
        "singles",
        "songs",
        "featuredOn",
    ]:
        items = extract_items(info.get(key))

        for item in items:
            title = show_release(item)

            if title and title not in releases:
                releases.append(title)

    return releases[:10]


def check_artist(expected, channel_id):
    try:
        info = ytmusic.get_artist(channel_id)

        returned_name = (
            info.get("name")
            or info.get("artist")
            or info.get("title")
        )

        subscribers = get_subscribers(info)

        releases = get_releases(info)

        if not names_match(expected, returned_name):
            return {
                "status": "RECHAZAR",
                "name": returned_name,
                "subscribers": subscribers,
                "releases": releases,
            }

        return {
            "status": "OK",
            "name": returned_name,
            "subscribers": subscribers,
            "releases": releases,
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "name": None,
            "subscribers": "?",
            "releases": [],
            "error": str(e)[:250],
        }


def main():
    print("=" * 75)
    print("PRUEBA DEFINITIVA — 37 ARTISTAS DE CUBATON MUSIC")
    print("=" * 75)
    print()

    ok = 0
    rejected = 0
    errors = 0

    for number, (artist, channel_id) in enumerate(
        ARTISTS.items(),
        start=1
    ):
        print()
        print("-" * 75)
        print(f"[{number}/37] {artist}")
        print("-" * 75)

        print("ID:", channel_id)

        result = check_artist(
            artist,
            channel_id
        )

        print(
            "YouTube Music:",
            result["name"]
        )

        print(
            "Seguidores:",
            result["subscribers"]
        )

        print(
            "RESULTADO:",
            result["status"]
        )

        if result["releases"]:
            print("Lanzamientos encontrados:")

            for release in result["releases"]:
                print("  -", release)
        else:
            print(
                "Lanzamientos encontrados: "
                "ninguno visible en esta consulta"
            )

        if result["status"] == "OK":
            ok += 1

        elif result["status"] == "RECHAZAR":
            rejected += 1

        else:
            errors += 1

            if result.get("error"):
                print(
                    "Error:",
                    result["error"]
                )

        time.sleep(0.8)

    print()
    print()
    print("=" * 75)
    print("RESUMEN")
    print("=" * 75)

    print("Artistas comprobados:", len(ARTISTS))
    print("OK:", ok)
    print("RECHAZADOS:", rejected)
    print("ERRORES:", errors)

    print()

    if ok == 37 and rejected == 0:
        print(
            "EXCELENTE: los 37 artistas fueron identificados correctamente."
        )
    else:
        print(
            "ATENCIÓN: todavía hay artistas que necesitan revisión."
        )

    print()
    print("=" * 75)
    print("FIN")
    print("=" * 75)


if __name__ == "__main__":
    main()
