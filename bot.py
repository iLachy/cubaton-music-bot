import os
import requests
from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = "@Cubaton_Music"

ARTIST_NAME = "Bebeshito"
ARTIST_CHANNEL_ID = "UCpVfWS-cPOE2sYqsFuuP_Qg"

# Lanzamiento que queremos probar
TEST_TITLE = "Enganchada Completa"


# ============================================================
# COMPROBAR TOKEN
# ============================================================

if not TELEGRAM_BOT_TOKEN:
    print("ERROR: No se encontró el secreto TELEGRAM_BOT_TOKEN.")
    raise SystemExit(1)


# ============================================================
# INICIALIZAR YOUTUBE MUSIC
# ============================================================

print("=" * 60)
print("PRUEBA DE PUBLICACIÓN — CUBATON MUSIC")
print("=" * 60)

print()
print(f"Consultando artista: {ARTIST_NAME}")

ytmusic = YTMusic()


# ============================================================
# CONSULTAR ARTISTA
# ============================================================

try:
    artista = ytmusic.get_artist(ARTIST_CHANNEL_ID)

except Exception as e:
    print()
    print("ERROR AL CONSULTAR EL ARTISTA:")
    print(e)
    raise SystemExit(1)


# ============================================================
# OBTENER LANZAMIENTOS
# ============================================================

lanzamientos = []

singles = artista.get("singles", {})
albums = artista.get("albums", {})

if isinstance(singles, dict):
    lanzamientos.extend(singles.get("results", []))

if isinstance(albums, dict):
    lanzamientos.extend(albums.get("results", []))


if not lanzamientos:
    print()
    print("ERROR: No se encontraron lanzamientos.")
    raise SystemExit(1)


# ============================================================
# BUSCAR EL LANZAMIENTO DE PRUEBA
# ============================================================

lanzamiento = None

for item in lanzamientos:

    titulo = str(item.get("title", "")).strip()

    if titulo.lower() == TEST_TITLE.lower():
        lanzamiento = item
        break


if not lanzamiento:
    print()
    print(f"ERROR: No se encontró el lanzamiento '{TEST_TITLE}'.")
    raise SystemExit(1)


# ============================================================
# DATOS DEL LANZAMIENTO
# ============================================================

titulo = lanzamiento.get("title", TEST_TITLE)
tipo = lanzamiento.get("type", "Single")
anio = lanzamiento.get("year", "")

browse_id = lanzamiento.get("browseId")

thumbnails = lanzamiento.get("thumbnails", [])

if not thumbnails:
    print()
    print("ERROR: El lanzamiento no tiene portada.")
    raise SystemExit(1)


# Usamos la imagen de mayor tamaño disponible
portada = thumbnails[-1].get("url")

if not portada:
    print()
    print("ERROR: No se encontró URL de portada.")
    raise SystemExit(1)


# ============================================================
# OBTENER VIDEO ID
# ============================================================

video_id = None

if browse_id:

    try:
        detalle = ytmusic.get_album(browse_id)

        tracks = detalle.get("tracks", [])

        if tracks:
            video_id = tracks[0].get("videoId")

    except Exception as e:
        print()
        print("ADVERTENCIA: No se pudo consultar el detalle del lanzamiento.")
        print(e)


# ============================================================
# URL DE YOUTUBE MUSIC
# ============================================================

if video_id:
    url_youtube = f"https://music.youtube.com/watch?v={video_id}"
else:
    # Fallback: búsqueda directa en YouTube Music
    consulta = f"{ARTIST_NAME} {titulo}"
    url_youtube = (
        "https://music.youtube.com/search?q="
        + requests.utils.quote(consulta)
    )


# ============================================================
# CONSTRUIR MENSAJE
# ============================================================

texto = (
    f"🎤 <b>{ARTIST_NAME}</b>\n"
    f"<blockquote>🎵 <b>{titulo}</b></blockquote>\n"
    f"📀 <b>Tipo:</b> {tipo}\n"
    f"🗓 {anio}\n"
    f"\n"
    f"@Cubaton_Music"
)


# ============================================================
# BOTÓN DE YOUTUBE MUSIC
# ============================================================

reply_markup = {
    "inline_keyboard": [
        [
            {
                "text": "▶️ Escuchar en YouTube Music",
                "url": url_youtube
            }
        ]
    ]
}


# ============================================================
# DATOS PARA TELEGRAM
# ============================================================

datos = {
    "chat_id": TELEGRAM_CHANNEL,
    "photo": portada,
    "caption": texto,
    "parse_mode": "HTML",
    "reply_markup": reply_markup
}


# ============================================================
# MOSTRAR INFORMACIÓN ANTES DE PUBLICAR
# ============================================================

print()
print("=" * 60)
print("PUBLICACIÓN DE PRUEBA")
print("=" * 60)

print(f"Artista: {ARTIST_NAME}")
print(f"Título: {titulo}")
print(f"Tipo: {tipo}")
print(f"Año: {anio}")
print(f"Video ID: {video_id}")
print(f"YouTube Music: {url_youtube}")
print(f"Portada: {portada}")

print()
print("Enviando publicación a Telegram...")


# ============================================================
# PUBLICAR EN TELEGRAM
# ============================================================

telegram_url = (
    f"https://api.telegram.org/bot"
    f"{TELEGRAM_BOT_TOKEN}/sendPhoto"
)

try:

    respuesta = requests.post(
        telegram_url,
        json=datos,
        timeout=30
    )

except Exception as e:

    print()
    print("ERROR DE CONEXIÓN CON TELEGRAM:")
    print(e)
    raise SystemExit(1)


# ============================================================
# COMPROBAR RESPUESTA
# ============================================================

print()
print("=" * 60)
print("RESPUESTA DE TELEGRAM")
print("=" * 60)

print(f"Código HTTP: {respuesta.status_code}")
print(respuesta.text)


if respuesta.ok:

    resultado = respuesta.json()

    if resultado.get("ok"):

        print()
        print("=" * 60)
        print("PUBLICACIÓN EXITOSA")
        print("=" * 60)
        print()
        print("La prueba fue publicada correctamente en:")
        print(TELEGRAM_CHANNEL)

    else:

        print()
        print("Telegram respondió con un error.")
        raise SystemExit(1)

else:

    print()
    print("ERROR: Telegram rechazó la publicación.")
    raise SystemExit(1)
