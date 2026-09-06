import os
import sys
import requests
from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN
# ============================================================

ARTIST_NAME = "Bebeshito"
ARTIST_CHANNEL_ID = "UCpVfWS-cPOE2sYqsFuuP_Qg"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = "@Cubaton_Music"


# ============================================================
# FUNCIONES
# ============================================================

def obtener_ultimo_lanzamiento():
    """
    Obtiene la información del artista desde YouTube Music
    y selecciona el lanzamiento más reciente disponible.
    """

    print(f"Consultando YouTube Music: {ARTIST_NAME}")

    ytmusic = YTMusic()

    artista = ytmusic.get_artist(ARTIST_CHANNEL_ID)

    albums = artista.get("albums", {})
    singles = artista.get("singles", {})

    lanzamientos = []

    # --------------------------------------------------------
    # Álbumes
    # --------------------------------------------------------

    if isinstance(albums, dict):
        for item in albums.get("results", []):
            if isinstance(item, dict):
                item["_tipo_lanzamiento"] = "Álbum"
                lanzamientos.append(item)

    # --------------------------------------------------------
    # Singles
    # --------------------------------------------------------

    if isinstance(singles, dict):
        for item in singles.get("results", []):
            if isinstance(item, dict):
                item["_tipo_lanzamiento"] = "Single"
                lanzamientos.append(item)

    if not lanzamientos:
        raise RuntimeError(
            "No se encontraron lanzamientos para el artista."
        )

    # --------------------------------------------------------
    # Mostrar los lanzamientos encontrados
    # --------------------------------------------------------

    print(f"Lanzamientos encontrados: {len(lanzamientos)}")

    for i, item in enumerate(lanzamientos[:10], start=1):
        titulo = item.get("title", "Sin título")
        tipo = item.get("_tipo_lanzamiento", "Lanzamiento")
        print(f"{i}. [{tipo}] {titulo}")

    # --------------------------------------------------------
    # El primer resultado de YouTube Music corresponde al
    # lanzamiento más reciente dentro de cada categoría.
    #
    # Priorizamos singles porque el objetivo principal del
    # canal son canciones nuevas.
    # --------------------------------------------------------

    if singles and isinstance(singles, dict):
        resultados_singles = singles.get("results", [])

        if resultados_singles:
            lanzamiento = resultados_singles[0]
            lanzamiento["_tipo_lanzamiento"] = "Single"
            return lanzamiento

    # Si no hay singles, utilizamos el álbum más reciente.

    if albums and isinstance(albums, dict):
        resultados_albums = albums.get("results", [])

        if resultados_albums:
            lanzamiento = resultados_albums[0]
            lanzamiento["_tipo_lanzamiento"] = "Álbum"
            return lanzamiento

    raise RuntimeError(
        "No fue posible determinar el lanzamiento más reciente."
    )


def obtener_imagen(lanzamiento):
    """
    Intenta obtener la mejor portada disponible.
    """

    thumbnails = lanzamiento.get("thumbnails", [])

    if thumbnails and isinstance(thumbnails, list):

        # Normalmente la última imagen es la de mayor resolución.
        for thumbnail in reversed(thumbnails):

            if isinstance(thumbnail, dict):
                url = thumbnail.get("url")

                if url:
                    return url

    return None


def obtener_url_youtube_music(lanzamiento):
    """
    Construye la URL de YouTube Music utilizando el browseId
    disponible en el lanzamiento.
    """

    browse_id = lanzamiento.get("browseId")

    if browse_id:
        return f"https://music.youtube.com/browse/{browse_id}"

    video_id = lanzamiento.get("videoId")

    if video_id:
        return f"https://music.youtube.com/watch?v={video_id}"

    return "https://music.youtube.com/"


def enviar_publicacion(lanzamiento):
    """
    Envía la publicación al canal de Telegram.
    """

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "No se encontró la variable TELEGRAM_BOT_TOKEN."
        )

    titulo = lanzamiento.get("title", "Sin título")
    tipo = lanzamiento.get("_tipo_lanzamiento", "Lanzamiento")

    portada = obtener_imagen(lanzamiento)
    url_youtube = obtener_url_youtube_music(lanzamiento)

    # --------------------------------------------------------
    # TEXTO DE LA PUBLICACIÓN
    # --------------------------------------------------------

    texto = (
        f"🎤 <b>{ARTIST_NAME}</b>\n"
        f"🎵 <b>{titulo}</b>\n"
        f"📀 Tipo: {tipo}"
    )

    # --------------------------------------------------------
    # BOTÓN
    # --------------------------------------------------------

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

    telegram_url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendPhoto"
    )

    # --------------------------------------------------------
    # PUBLICAR CON PORTADA
    # --------------------------------------------------------

    if portada:

        datos = {
            "chat_id": TELEGRAM_CHANNEL,
            "photo": portada,
            "caption": texto,
            "parse_mode": "HTML",
            "reply_markup": str(reply_markup).replace("'", '"')
        }

        respuesta = requests.post(
            telegram_url,
            data=datos,
            timeout=30
        )

    else:
        # ----------------------------------------------------
        # Si por alguna razón YouTube Music no proporciona
        # portada, enviamos el mensaje igualmente.
        # ----------------------------------------------------

        telegram_url_text = (
            f"https://api.telegram.org/bot"
            f"{TELEGRAM_BOT_TOKEN}/sendMessage"
        )

        datos = {
            "chat_id": TELEGRAM_CHANNEL,
            "text": texto,
            "parse_mode": "HTML",
            "reply_markup": str(reply_markup).replace("'", '"')
        }

        respuesta = requests.post(
            telegram_url_text,
            data=datos,
            timeout=30
        )

    # --------------------------------------------------------
    # COMPROBAR RESPUESTA
    # --------------------------------------------------------

    if not respuesta.ok:

        print("ERROR DE TELEGRAM")
        print(respuesta.text)

        raise RuntimeError(
            f"Telegram devolvió HTTP {respuesta.status_code}"
        )

    resultado = respuesta.json()

    if not resultado.get("ok"):
        print("Telegram rechazó la publicación:")
        print(resultado)

        raise RuntimeError(
            "Telegram no pudo enviar la publicación."
        )

    print()
    print("==========================================")
    print("PUBLICACIÓN ENVIADA CORRECTAMENTE")
    print("==========================================")
    print(f"Artista: {ARTIST_NAME}")
    print(f"Título: {titulo}")
    print(f"Tipo: {tipo}")
    print(f"YouTube Music: {url_youtube}")
    print("==========================================")


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print("==========================================")
    print("PRUEBA DE PUBLICACIÓN - CUBATON MUSIC")
    print("==========================================")
    print()

    try:

        lanzamiento = obtener_ultimo_lanzamiento()

        print()
        print("Lanzamiento seleccionado:")
        print(
            lanzamiento.get(
                "title",
                "Sin título"
            )
        )

        print()

        enviar_publicacion(lanzamiento)

    except Exception as error:

        print()
        print("==========================================")
        print("ERROR")
        print("==========================================")
        print(str(error))
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()
