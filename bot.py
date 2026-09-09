import os
import json
from io import BytesIO

import requests
from PIL import Image
from ytmusicapi import YTMusic

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@Cubaton_Music"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

VIDEO_ID = "AU_l1Rn_nJI"
ALBUM_ID = "MPREb_2vLxqqdb9hf"

TITLE = "Pal Piso (feat. El Lápiz De Oro)"
ARTISTS = "LA R, Musteerifa, Vittorio Di Benedetto"
YEAR = "2026"
YTM_URL = f"https://music.youtube.com/watch?v={VIDEO_ID}"


def main():
    print("=" * 72)
    print("PRUEBA DE PUBLICACIÓN — PAL PISO POR album.id")
    print("=" * 72)
    print()
    print("state/releases.json NO será leído ni modificado.")
    print("Se usará EXCLUSIVAMENTE get_album() con el album.id conocido.")
    print("No se usará get_song() ni search() para obtener la portada.")
    print("La imagen será enviada a Telegram SIN modificarla.")
    print()

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No existe el secreto TELEGRAM_BOT_TOKEN.")
        return

    ytmusic = YTMusic()

    print("[1] CONSULTANDO get_album() DIRECTAMENTE")
    print(f"Album ID: {ALBUM_ID}")
    album = ytmusic.get_album(ALBUM_ID)

    if not isinstance(album, dict):
        print("ERROR: get_album() no devolvió un objeto válido.")
        return

    print(f"Título devuelto: {album.get('title')!r}")
    print(f"Tipo: {album.get('type')!r}")
    print(f"Año: {album.get('year')!r}")

    thumbnails = album.get("thumbnails") or []
    if not thumbnails:
        print("ERROR: El álbum no contiene thumbnails.")
        return

    # Elegir la thumbnail de mayor resolución REAL devuelta por YT Music.
    candidatas = []
    for thumb in thumbnails:
        if not isinstance(thumb, dict) or not thumb.get("url"):
            continue
        try:
            w = int(thumb.get("width") or 0)
        except (TypeError, ValueError):
            w = 0
        try:
            h = int(thumb.get("height") or 0)
        except (TypeError, ValueError):
            h = 0
        candidatas.append((max(w, h), w, h, thumb["url"]))

    if not candidatas:
        print("ERROR: No hay thumbnails utilizables.")
        return

    candidatas.sort(reverse=True)
    _, width, height, image_url = candidatas[0]

    print()
    print("[2] PORTADA SELECCIONADA DESDE get_album()")
    print(f"Resolución declarada: {width}x{height}")
    print(f"URL: {image_url}")
    print()

    print("[3] DESCARGANDO ESA MISMA IMAGEN PARA ENVIARLA")
    response = requests.get(image_url, timeout=30)
    response.raise_for_status()

    image_bytes = response.content
    image = Image.open(BytesIO(image_bytes))
    print(f"Dimensiones reales descargadas: {image.width}x{image.height}")
    print(f"Formato real descargado: {image.format}")
    print("La imagen NO será redimensionada, recortada ni recomprimida.")
    print()

    caption = (
        f"🎤 <b>{ARTISTS}</b>\n"
        f"<blockquote>🎵 <b>Pal Piso (feat. El Lápiz De Oro)</b></blockquote>\n"
        f"📀 <i>Single</i>\n"
        f"🗓 {YEAR}\n\n"
        f"@Cubaton_Music"
    )

    reply_markup = {
        "inline_keyboard": [[
            {
                "text": "▶️ Escuchar en YouTube Music",
                "url": YTM_URL,
            }
        ]]
    }

    print("[4] ENVIANDO A TELEGRAM")
    print(f"Destino: {TELEGRAM_CHAT_ID}")

    telegram_response = requests.post(
        f"{TELEGRAM_API}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(reply_markup, ensure_ascii=False),
        },
        files={
            "photo": ("pal_piso_album.jpg", image_bytes, "image/jpeg")
        },
        timeout=60,
    )

    if not telegram_response.ok:
        print("ERROR DE TELEGRAM:")
        print(telegram_response.text)
        return

    data = telegram_response.json()
    if not data.get("ok"):
        print("TELEGRAM DEVOLVIÓ ERROR:")
        print(data)
        return

    print("PUBLICACIÓN ENVIADA CORRECTAMENTE")
    print()
    print("=" * 72)
    print("FIN DE LA PRUEBA")
    print("state/releases.json NO FUE LEÍDO NI MODIFICADO.")
    print("La portada utilizada fue exclusivamente la obtenida mediante get_album().")
    print("=" * 72)


if __name__ == "__main__":
    main()
