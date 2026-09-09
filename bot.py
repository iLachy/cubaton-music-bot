import os
import json
from io import BytesIO

import requests
from PIL import Image, ImageOps


# ============================================================
# CONFIGURACIÓN DE PRUEBA
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@Cubaton_Music"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Canción exacta proporcionada por el usuario.
VIDEO_ID = "AU_l1Rn_nJI"
YOUTUBE_MUSIC_URL = (
    f"https://music.youtube.com/watch?v={VIDEO_ID}"
)

# Metadata verificada externamente para esta prueba.
TITULO = "Pal Piso"
ARTISTAS = "LA R, Musteerifa, Vittorio Di Benedetto"
TIPO = "Single"
ANIO = "2026"


# ============================================================
# PREPARAR PORTADA CUADRADA
# ============================================================

def preparar_portada():
    """Descarga la miniatura y la convierte realmente en 1000x1000."""

    thumbnail_url = (
        f"https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg"
    )

    respuesta = requests.get(
        thumbnail_url,
        timeout=30,
    )
    respuesta.raise_for_status()

    imagen = Image.open(
        BytesIO(respuesta.content)
    ).convert("RGB")

    imagen_cuadrada = ImageOps.fit(
        imagen,
        (1000, 1000),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )

    if imagen_cuadrada.size != (1000, 1000):
        raise RuntimeError(
            f"La portada no quedó cuadrada: {imagen_cuadrada.size}"
        )

    buffer = BytesIO()
    imagen_cuadrada.save(
        buffer,
        format="JPEG",
        quality=95,
        optimize=True,
    )
    buffer.seek(0)

    return buffer


# ============================================================
# PUBLICAR PRUEBA
# ============================================================

def publicar_prueba():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "No existe el secreto TELEGRAM_BOT_TOKEN."
        )

    caption = (
        f"🎤 <b>{ARTISTAS}</b>\n"
        f"<blockquote>🎵 <b>{TITULO}</b></blockquote>\n"
        f"📀 <i>{TIPO}</i>\n"
        f"🗓 {ANIO}\n"
        f"\n"
        f"@Cubaton_Music"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "▶️ Escuchar en YouTube Music",
                    "url": YOUTUBE_MUSIC_URL,
                }
            ]
        ]
    }

    print("=" * 60)
    print("CUBATON MUSIC BOT - PRUEBA DIRECTA")
    print("=" * 60)
    print(f"Video ID: {VIDEO_ID}")
    print(f"Título: {TITULO}")
    print(f"Artistas: {ARTISTAS}")
    print(f"Tipo: {TIPO}")
    print(f"Año: {ANIO}")
    print("Estado: NO SE MODIFICARÁ")
    print("=" * 60)

    portada = preparar_portada()

    respuesta = requests.post(
        f"{TELEGRAM_API}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(
                reply_markup,
                ensure_ascii=False,
            ),
        },
        files={
            "photo": (
                f"{VIDEO_ID}.jpg",
                portada,
                "image/jpeg",
            )
        },
        timeout=60,
    )

    if not respuesta.ok:
        raise RuntimeError(
            f"Telegram HTTP {respuesta.status_code}: {respuesta.text}"
        )

    datos = respuesta.json()

    if not datos.get("ok"):
        raise RuntimeError(str(datos))

    print("PUBLICACIÓN ENVIADA CORRECTAMENTE")
    print("state/releases.json NO FUE LEÍDO NI MODIFICADO.")


if __name__ == "__main__":
    try:
        publicar_prueba()
    except Exception as error:
        print(f"ERROR: {error}")
        raise
