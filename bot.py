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
    Obtiene los lanzamientos de Bebeshito desde YouTube Music
    y selecciona el single más reciente.
    """

    print(f"Consultando YouTube Music: {ARTIST_NAME}")

    ytmusic = YTMusic()

    artista = ytmusic.get_artist(ARTIST_CHANNEL_ID)

    albums = artista.get("albums", {})
    singles = artista.get("singles", {})

    # --------------------------------------------------------
    # Priorizamos Singles
    # --------------------------------------------------------

    if isinstance(singles, dict):
        resultados = singles.get("results", [])

        if resultados:
            lanzamiento = resultados[0].copy()
            lanzamiento["_tipo_lanzamiento"] = "Single"

            print(f"Lanzamiento seleccionado: {lanzamiento.get('title')}")
            return lanzamiento

    # --------------------------------------------------------
    # Si no hay singles, utilizamos el álbum más reciente
    # --------------------------------------------------------

    if isinstance(albums, dict):
        resultados = albums.get("results", [])

        if resultados:
            lanzamiento = resultados[0].copy()
            lanzamiento["_tipo_lanzamiento"] = "Álbum"

            print(f"Lanzamiento seleccionado: {lanzamiento.get('title')}")
            return lanzamiento

    raise RuntimeError(
        "No se encontró ningún lanzamiento."
    )


def obtener_imagen(lanzamiento):
    """
    Obtiene la portada de mayor resolución disponible.
    """

    thumbnails = lanzamiento.get("thumbnails", [])

    if isinstance(thumbnails, list) and thumbnails:

        for thumbnail in reversed(thumbnails):

            if isinstance(thumbnail, dict):

                url = thumbnail.get("url")

                if url:
                    return url

    return None


def obtener_fecha(lanzamiento):
    """
    Intenta obtener la fecha de lanzamiento proporcionada
    por YouTube Music.

    Devuelve la fecha en formato D/M/A.
    """

    fecha = lanzamiento.get("releaseDate")

    if not fecha:
        fecha = lanzamiento.get("release_date")

    if not fecha:
        return None

    # --------------------------------------------------------
    # YouTube Music puede devolver una fecha ISO:
    # YYYY-MM-DD
    # --------------------------------------------------------

    if isinstance(fecha, str):

        partes = fecha.split("-")

        if len(partes) >= 3:

            try:
                año = int(partes[0])
                mes = int(partes[1])
                dia = int(partes[2])

                return f"{dia}/{mes}/{año}"

            except ValueError:
                pass

        # ----------------------------------------------------
        # En caso de que ya venga en otro formato
        # ----------------------------------------------------

        return fecha

    return None


def obtener_url_youtube_music(lanzamiento):
    """
    Obtiene el enlace directo de YouTube Music.
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
    Publica el lanzamiento en Telegram utilizando HTML.
    """

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "No se encontró TELEGRAM_BOT_TOKEN."
        )

    titulo = lanzamiento.get(
        "title",
        "Sin título"
    )

    tipo = lanzamiento.get(
        "_tipo_lanzamiento",
        "Lanzamiento"
    )

    portada = obtener_imagen(lanzamiento)

    fecha = obtener_fecha(lanzamiento)

    url_youtube = obtener_url_youtube_music(
        lanzamiento
    )

    # --------------------------------------------------------
    # CONSTRUIR MENSAJE
    # --------------------------------------------------------

    texto = (
        f"🎤 <b>{ARTIST_NAME}</b>\n\n"
        f"🎵 <blockquote><b>{titulo}</b></blockquote>\n\n"
        f"📀 Tipo: {tipo}"
    )

    # --------------------------------------------------------
    # FECHA
    # --------------------------------------------------------

    if fecha:
        texto += f"\n🗓 {fecha}"

    # --------------------------------------------------------
    # BOTÓN DE YOUTUBE MUSIC
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

    # --------------------------------------------------------
    # TELEGRAM API
    # --------------------------------------------------------

    if portada:

        telegram_url = (
            f"https://api.telegram.org/bot"
            f"{TELEGRAM_BOT_TOKEN}/sendPhoto"
        )

        datos = {
            "chat_id": TELEGRAM_CHANNEL,
            "photo": portada,
            "caption": texto,
            "parse_mode": "HTML",
            "reply_markup": reply_markup
        }

    else:

        telegram_url = (
            f"https://api.telegram.org/bot"
            f"{TELEGRAM_BOT_TOKEN}/sendMessage"
        )

        datos = {
            "chat_id": TELEGRAM_CHANNEL,
            "text": texto,
            "parse_mode": "HTML",
            "reply_markup": reply_markup
        }

    # --------------------------------------------------------
    # ENVIAR
    # --------------------------------------------------------

    respuesta = requests.post(
        telegram_url,
        data=datos,
        timeout=30
    )

    # --------------------------------------------------------
    # COMPROBAR RESULTADO
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
            "Telegram no pudo publicar el mensaje."
        )

    print()
    print("==========================================")
    print("PUBLICACIÓN ENVIADA CORRECTAMENTE")
    print("==========================================")
    print(f"Artista: {ARTIST_NAME}")
    print(f"Título: {titulo}")
    print(f"Tipo: {tipo}")
    print(f"Fecha: {fecha or 'No disponible'}")
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
