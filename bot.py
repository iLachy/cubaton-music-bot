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
# YOUTUBE MUSIC
# ============================================================

def obtener_ultimo_lanzamiento():

    print(f"Consultando YouTube Music: {ARTIST_NAME}")

    ytmusic = YTMusic()

    artista = ytmusic.get_artist(ARTIST_CHANNEL_ID)

    singles = artista.get("singles", {})
    albums = artista.get("albums", {})

    # --------------------------------------------------------
    # Preferimos el single más reciente
    # --------------------------------------------------------

    if isinstance(singles, dict):

        resultados = singles.get("results", [])

        if resultados:

            lanzamiento = resultados[0].copy()
            lanzamiento["_tipo_lanzamiento"] = "Single"

            print(
                f"Lanzamiento seleccionado: "
                f"{lanzamiento.get('title', 'Sin título')}"
            )

            return lanzamiento

    # --------------------------------------------------------
    # Si no hay singles, utilizamos el álbum más reciente
    # --------------------------------------------------------

    if isinstance(albums, dict):

        resultados = albums.get("results", [])

        if resultados:

            lanzamiento = resultados[0].copy()
            lanzamiento["_tipo_lanzamiento"] = "Álbum"

            print(
                f"Lanzamiento seleccionado: "
                f"{lanzamiento.get('title', 'Sin título')}"
            )

            return lanzamiento

    raise RuntimeError(
        "No se encontró ningún lanzamiento."
    )


# ============================================================
# PORTADA
# ============================================================

def obtener_imagen(lanzamiento):

    thumbnails = lanzamiento.get("thumbnails", [])

    if isinstance(thumbnails, list):

        for thumbnail in reversed(thumbnails):

            if isinstance(thumbnail, dict):

                url = thumbnail.get("url")

                if url:
                    return url

    return None


# ============================================================
# FECHA
# ============================================================

def obtener_fecha(lanzamiento):

    posibles_campos = [
        "releaseDate",
        "release_date",
        "date"
    ]

    fecha = None

    for campo in posibles_campos:

        valor = lanzamiento.get(campo)

        if valor:
            fecha = valor
            break

    if not fecha:
        return None

    if not isinstance(fecha, str):
        return None

    # --------------------------------------------------------
    # Formato esperado:
    # YYYY-MM-DD
    # --------------------------------------------------------

    partes = fecha.split("-")

    if len(partes) >= 3:

        try:

            año = int(partes[0])
            mes = int(partes[1])
            dia = int(partes[2])

            return f"{dia}/{mes}/{año}"

        except ValueError:
            pass

    return fecha


# ============================================================
# URL YOUTUBE MUSIC
# ============================================================

def obtener_url_youtube_music(lanzamiento):

    browse_id = lanzamiento.get("browseId")

    if browse_id:

        return (
            f"https://music.youtube.com/browse/"
            f"{browse_id}"
        )

    video_id = lanzamiento.get("videoId")

    if video_id:

        return (
            f"https://music.youtube.com/watch?v="
            f"{video_id}"
        )

    return "https://music.youtube.com/"


# ============================================================
# ESCAPAR HTML
# ============================================================

def escapar_html(texto):

    if texto is None:
        return ""

    texto = str(texto)

    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")

    return texto


# ============================================================
# PUBLICAR EN TELEGRAM
# ============================================================

def enviar_publicacion(lanzamiento):

    if not TELEGRAM_BOT_TOKEN:

        raise RuntimeError(
            "No se encontró la variable "
            "TELEGRAM_BOT_TOKEN."
        )

    titulo = escapar_html(
        lanzamiento.get(
            "title",
            "Sin título"
        )
    )

    artista = escapar_html(
        ARTIST_NAME
    )

    tipo = escapar_html(
        lanzamiento.get(
            "_tipo_lanzamiento",
            "Lanzamiento"
        )
    )

    fecha = obtener_fecha(lanzamiento)

    portada = obtener_imagen(lanzamiento)

    url_youtube = obtener_url_youtube_music(
        lanzamiento
    )

    # --------------------------------------------------------
    # MENSAJE
    #
    # Usamos <blockquote> para crear la cita de Telegram.
    # El título permanece en negrita.
    # --------------------------------------------------------

    texto = (
        f"🎤 <b>{artista}</b>\n\n"
        f"🎵 <blockquote><b>{titulo}</b></blockquote>\n\n"
        f"📀 Tipo: {tipo}"
    )

    if fecha:

        texto += f"\n🗓 {fecha}"

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

    # --------------------------------------------------------
    # PREPARAR PETICIÓN
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
    # ENVIAR PETICIÓN
    #
    # json= hace que requests convierta correctamente
    # reply_markup al formato JSON que Telegram espera.
    # --------------------------------------------------------

    respuesta = requests.post(
        telegram_url,
        json=datos,
        timeout=30
    )

    print()
    print("Respuesta de Telegram:")
    print(respuesta.text)
    print()

    # --------------------------------------------------------
    # COMPROBAR
    # --------------------------------------------------------

    if not respuesta.ok:

        raise RuntimeError(
            f"Telegram devolvió HTTP "
            f"{respuesta.status_code}"
        )

    resultado = respuesta.json()

    if not resultado.get("ok"):

        raise RuntimeError(
            "Telegram rechazó la publicación."
        )

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
