#!/usr/bin/env python3

import json
import sys
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


def get_json(url: str):
    print(f"\n>>> GET {url}\n")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    print(f">>> HTTP {response.status_code}\n")

    response.raise_for_status()

    return response.json()


def main():

    if len(sys.argv) != 2:
        print(
            "Uso:\n"
            'python deezer_debug.py "URL_DEEZER"'
        )
        sys.exit(1)

    deezer_url = sys.argv[1]

    # ---------------------------------------------------------
    # Extraer ID del álbum desde la URL
    # ---------------------------------------------------------

    parts = deezer_url.rstrip("/").split("/")

    if len(parts) < 2:
        print("URL inválida.")
        sys.exit(1)

    resource_type = parts[-2]
    resource_id = parts[-1].split("?")[0]

    if resource_type != "album":
        print(
            "Esta prueba está preparada para una URL /album/."
        )
        sys.exit(1)

    # ---------------------------------------------------------
    # Obtener álbum completo
    # ---------------------------------------------------------

    album_url = f"{DEEZER_API}/album/{resource_id}"

    album = get_json(album_url)

    print("=" * 80)
    print("JSON COMPLETO DEL ÁLBUM")
    print("=" * 80)

    print(
        json.dumps(
            album,
            ensure_ascii=False,
            indent=2,
        )
    )

    # ---------------------------------------------------------
    # Obtener las pistas del álbum
    # ---------------------------------------------------------

    tracks = album.get("tracks", {})

    track_list = tracks.get("data", [])

    print("\n")
    print("=" * 80)
    print("PISTAS DEL ÁLBUM")
    print("=" * 80)

    print(
        json.dumps(
            track_list,
            ensure_ascii=False,
            indent=2,
        )
    )

    # ---------------------------------------------------------
    # Si existe una pista, consultar también /track/{id}
    # ---------------------------------------------------------

    if track_list:

        track_id = track_list[0].get("id")

        if track_id:

            track_url = f"{DEEZER_API}/track/{track_id}"

            track = get_json(track_url)

            print("\n")
            print("=" * 80)
            print(f"JSON COMPLETO DE LA PISTA {track_id}")
            print("=" * 80)

            print(
                json.dumps(
                    track,
                    ensure_ascii=False,
                    indent=2,
                )
            )


if __name__ == "__main__":
    main()