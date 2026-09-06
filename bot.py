from ytmusicapi import YTMusic
import re
import time

ytmusic = YTMusic()

ARTISTS = [
    "Bebeshito",
    "Charly & Johayron",
    "Dany Ome",
    "Kevincito El 13",
    "Wampi",
    "El Taiger",
    "Ja Rulay",
    "L Kimii",
    "El Dray",
    "Mauro y El Pitu",
    "Yirow Y El Tingo",
    "Nany La Kbra",
    "Ya Ice Dilan",
    "Rey Tony",
    "Baby Maikol",
    "Payaso X Ley",
    "Kaly Y Kowa",
    "Wildey",
    "Wow Popy",
    "Talent Fuego",
    "Mawell",
    "Harryson",
    "El Chulo",
    "Fixty Ordara",
    "El Kamel",
    "Velito el Bufón",
    "Helabusador",
    "Un Titico",
    "Musteerifa",
    "Chocolate MC",
    "El Chacal",
    "El Micha",
    "Yomil",
    "Jacob Forever",
    "Gente de Zona",
    "La Diosa",
    "Seidy La Niña",
]

# IDs candidatos encontrados anteriormente.
# NO añadimos DJs, productores ni artistas fuera de la lista.
CANDIDATES = {
    "Bebeshito": [
        "UCpVfWS-cPOE2sYqsFuuP_Qg",
        "UCw-vCTQtXIE-S40-7kva36A",
    ],
    "Charly & Johayron": [
        "UCnwEtOQyXJUUuBhcTgImdfQ",
    ],
    "Dany Ome": [
        "UCJQEm9t4KjDn-I8Fahf4Uqw",
        "UCuBGNyEpfrbbhZ3r3vIjnfg",
    ],
    "Kevincito El 13": [
        "UCDxpdRMANSbNf_Oy3FwBCRw",
        "UC1lU2Dft38ZJRPiX3UHPxJw",
    ],
    "Wampi": [
        "UCbfzw8u1lCwDMv443StJEOw",
        "UCpEUxFe9-QlnjiCcNkc0zjA",
    ],
    "El Taiger": [
        "UCoYtt7bGCV5RyUweyQgqQ4A",
        "UC7zf0CWAbFPbzTitZ_nd_qg",
    ],
    "Ja Rulay": [
        "UCcaU4COep7mj8kbXwS24JFQ",
        "UC5HZiMlDJb5nkotDctm-RGw",
    ],
    "L Kimii": [
        "UCMyQosiL8iVUtXPIm1UZJQg",
    ],
    "El Dray": [
        "UC4kpn8y8QXYXmyDn8HJKD8Q",
    ],
    "Mauro y El Pitu": [
        "UCvN1mRFfAfWYTiIkM70qUWA",
    ],
    "Yirow Y El Tingo": [
        "UCEq3_5h1Xi_vLbytP7OzuNA",
    ],
    "Nany La Kbra": [
        "UCG4lSNdNx_LuLnN2EW6uWwQ",
    ],
    "Ya Ice Dilan": [
        "UC9aJbR9Q8nscvZaMw_cH4Ww",
    ],
    "Rey Tony": [
        "UCDhExL0uVtumv_DEjPPq5qg",
    ],
    "Baby Maikol": [
        "UCP5R6Mgbk_bgtgzZguLNKdA",
        "UCoZ9SeN4QehLThj85YsdkVA",
    ],
    "Payaso X Ley": [
        "UCauTaqBvFqqqJTu3B4Wc1GA",
        "UCz4FLcaulTBuDmXKYnO5dTg",
    ],
    "Kaly Y Kowa": [
        "UCSfR51myQhs2ZcdzrWo0Z4w",
        "UC40wOBt1kO3U5swWGag9PFw",
    ],
    "Wildey": [
        "UCmFS-VSa4Wf3F1wdWS-8p_g",
        "UCK7SfNGK-9Z-g1DI3csyviQ",
    ],
    "Wow Popy": [
        "UCtFkN8UFxT_MuNdySlfuFuA",
        "UC7mIT0NJj460QeI-DUH75RA",
    ],
    "Talent Fuego": [
        "UC0dVmcXfNa7lVeUBve3_FXw",
        "UCEU2UP8DamKzULakxOwsxAA",
    ],
    "Mawell": [
        "UCL6P-jUDZEKBA-Lb6WFccWg",
        "UCAmgphQnzSogyskD7d5skng",
    ],
    "Harryson": [
        "UC2ihX5uoblnN4wsA-ayIAAA",
    ],
    "El Chulo": [
        "UCiT8VNdnpeYnCTPJZoqym9g",
        "UCOx3mWPFzMwwfn5h_obJOaw",
    ],
    "Fixty Ordara": [
        "UCDHDCbVOQywsLCsCZ8PH-AA",
    ],
    "El Kamel": [
        "UCPnWcazEV7QM0H7qBx6NVXg",
    ],
    "Velito el Bufón": [
        "UCRA9cRfAJXuxDRcFnoB7pwg",
        "UC9LVti7i-zRT1nNsC8V2vbQ",
    ],
    "Helabusador": [
        "UC89ct8d1ZKEXS03nSpntgPg",
    ],
    "Un Titico": [
        "UCT2KiGFSPZIF3DR9UIN2fYw",
    ],
    "Musteerifa": [
        "UCiT8PzlQqtPC7lWFh3--4jw",
    ],
    "Chocolate MC": [
        "UCYVuThmAmbXxk1o9Un5Cc_w",
    ],
    "El Chacal": [
        "UCJt4IsSmUjqTaamhCJoKK_g",
        "UCifSmywTB4gu0_Qki0pqLQg",
    ],
    "El Micha": [
        "UCHhrMSqe_C1E_JBEz3mRlew",
    ],
    "Yomil": [
        "UCPfXwOpwRIbVsqqTsgt4i5g",
        "UC6-tqQHbPmApR086XphYTtg",
    ],
    "Jacob Forever": [
        "UCJ1-Pwsroy-gzMqlfKDF4Hg",
        "UCACtbFEthbvnK7eC2EESvvg",
    ],
    "Gente de Zona": [
        "UCl2KQVc_GFH081i7b9CJQug",
    ],
    "La Diosa": [
        "UChbVOQHgq01JoHY4axuWV0A",
        "UCLuoDT4ln0HhExK_o5ieIzg",
    ],
    "Seidy La Niña": [
        "UCFqYfgj_7h3ZUkBnyYS-TFg",
        "UCSBAeH8Qg4kq1AiN85zUiRA",
    ],
}


def normalize(text):
    if not text:
        return ""

    text = text.lower()

    replacements = {
        "&": "and",
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


def compatible(expected, returned):
    if not returned:
        return False

    e = normalize(expected)
    r = normalize(returned)

    # Coincidencia directa
    if e == r:
        return True

    # Uno contiene al otro
    if e in r or r in e:
        return True

    # Comparación por palabras importantes
    e_words = set(e.split())
    r_words = set(r.split())

    important = {
        "el", "la", "los", "las",
        "y", "de", "mc", "official",
        "oficial", "music", "musica"
    }

    e_words -= important
    r_words -= important

    if e_words and r_words:
        overlap = len(e_words & r_words)

        if overlap >= max(1, min(len(e_words), len(r_words))):
            return True

    return False


def get_subscribers(info):
    return (
        info.get("subscribers")
        or info.get("subscriberCount")
        or info.get("subscribersText")
        or "?"
    )


def get_description(info):
    description = info.get("description")

    if not description:
        return ""

    description = str(description).replace("\n", " ").strip()

    if len(description) > 180:
        description = description[:180] + "..."

    return description


def get_releases(info):
    releases = []

    possible_keys = [
        "albums",
        "singles",
        "songs",
        "featuredOn",
    ]

    for key in possible_keys:
        data = info.get(key)

        if not data:
            continue

        if isinstance(data, dict):
            data = data.get("results", [])

        if not isinstance(data, list):
            continue

        for item in data:
            if not isinstance(item, dict):
                continue

            title = (
                item.get("title")
                or item.get("name")
            )

            if title and title not in releases:
                releases.append(title)

    return releases[:8]


def check_candidate(expected, candidate_id):
    try:
        info = ytmusic.get_artist(candidate_id)

        returned_name = (
            info.get("name")
            or info.get("artist")
            or info.get("title")
        )

        subscribers = get_subscribers(info)
        description = get_description(info)
        releases = get_releases(info)

        ok = compatible(expected, returned_name)

        return {
            "id": candidate_id,
            "name": returned_name,
            "subscribers": subscribers,
            "description": description,
            "releases": releases,
            "status": "OK" if ok else "RECHAZAR",
        }

    except Exception as e:
        return {
            "id": candidate_id,
            "name": None,
            "subscribers": "?",
            "description": "",
            "releases": [],
            "status": "ERROR",
            "error": str(e)[:180],
        }


def main():
    print("=" * 70)
    print("VALIDACIÓN DIRECTA DE IDs — CUBATON MUSIC")
    print("=" * 70)
    print()
    print("Artistas incluidos:", len(ARTISTS))
    print("Solo se utilizan los 37 artistas definidos.")
    print()

    total_ok = 0
    total_rejected = 0
    total_errors = 0
    total_no_candidates = 0

    confirmed = {}

    for number, artist in enumerate(ARTISTS, start=1):

        print()
        print("-" * 70)
        print(f"[{number}/{len(ARTISTS)}] {artist}")
        print("-" * 70)

        candidates = CANDIDATES.get(artist, [])

        if not candidates:
            print("SIN CANDIDATOS")
            total_no_candidates += 1
            continue

        valid_for_artist = []

        for candidate_id in candidates:

            print()
            print("ID candidato:", candidate_id)

            result = check_candidate(artist, candidate_id)

            print("Nombre YouTube Music:", result["name"])
            print("Seguidores:", result["subscribers"])

            if result["description"]:
                print("Descripción:", result["description"])

            if result["releases"]:
                print("Lanzamientos:")
                for release in result["releases"]:
                    print("  -", release)

            print("RESULTADO:", result["status"])

            if result["status"] == "OK":
                valid_for_artist.append(result)
                total_ok += 1

            elif result["status"] == "RECHAZAR":
                total_rejected += 1

            else:
                total_errors += 1

            time.sleep(0.8)

        if valid_for_artist:
            confirmed[artist] = valid_for_artist

    print()
    print()
    print("=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)

    print("Artistas de la lista:", len(ARTISTS))
    print("Candidatos OK:", total_ok)
    print("Candidatos rechazados:", total_rejected)
    print("Errores:", total_errors)
    print("Artistas sin candidatos:", total_no_candidates)

    print()
    print("=" * 70)
    print("CANDIDATOS VÁLIDOS POR ARTISTA")
    print("=" * 70)

    for artist in ARTISTS:

        valid = confirmed.get(artist, [])

        if not valid:
            print(f"{artist} -> SIN CANDIDATO CONFIRMADO")
            continue

        print()
        print(f"{artist}:")

        for item in valid:
            print(
                f"  {item['id']} -> "
                f"{item['name']} | "
                f"Seguidores: {item['subscribers']}"
            )

    print()
    print("=" * 70)
    print("FIN DE LA VALIDACIÓN")
    print("=" * 70)


if __name__ == "__main__":
    main()
