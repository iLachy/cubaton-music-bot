import os
import sys
import requests
from datetime import datetime
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

def obtener_fecha(lanzamiento, ytmusic):

    """
    Intenta obtener la fecha real del lanzamiento.

    Primero revisa los campos disponibles directamente
    en el lanzamiento.

    Si no existe, intenta consultar el detalle del
    lanzamiento mediante su browseId.
    """

    campos_fecha = [
        "releaseDate",
        "release_date",
        "release_date_text",
        "date"
    ]

    # --------------------------------------------------------
    # 1. Buscar fecha directamente
    # --------------------------------------------------------

    for campo in campos_fecha:

        valor = lanzamiento.get(campo)

        if valor:

            fecha = convertir_fecha(valor)

            if fecha:
                return fecha

    # --------------------------------------------------------
    # 2. Consultar detalles mediante browseId
    # --------------------------------------------------------

    browse_id = lanzamiento.get("browseId")

    if browse_id:

        try:

            print(
                f"Consultando detalles del lanzamiento: "
                f"{browse_id}"
            )

            detalle = ytmusic.get_album(
                browse_id
            )

            # ------------------------------------------------
            # Buscar campos de fecha en el detalle
            # ------------------------------------------------

            for campo in campos_fecha:

                valor = detalle.get(campo)

                if valor:

                    fecha = convertir_fecha(valor)

                    if fecha:
                        return fecha

            # ------------------------------------------------
            # Algunas respuestas pueden guardar la fecha
            # dentro de otra estructura.
            # ------------------------------------------------

            if isinstance(detalle, dict):

                for clave, valor in detalle.items():

                    nombre = str(clave).lower()

                    if (
                        "date" in nombre
                        or "release" in nombre
                    ):

                        fecha = convertir_fecha(valor)

                        if fecha:
                            return fecha

        except Exception as error:

            print(
                "No fue posible obtener la fecha "
                f"desde el detalle: {error}"
            )

    return None


def convertir_fecha(valor):

    """
    Convierte distintos formatos posibles de fecha
    a D/M/A.
    """

    if not isinstance(valor, str):
        return None

    valor = valor.strip()

    # --------------------------------------------------------
    # YYYY-MM-DD
    # --------------------------------------------------------

    try:

        fecha = datetime.strptime(
            valor[:10],
            "%Y-%m-%d"
        )

        return (
            f"{fecha.day}/"
            f"{fecha.month}/"
            f"{fecha.year}"
        )

    except ValueError:
        pass

    # --------------------------------------------------------
    # YYYY/MM/DD
    # --------------------------------------------------------

    try:

        fecha = datetime.strptime(
            valor[:10],
            "%Y/%m/%d"
        )

        return (
            f"{fecha.day}/"
            f"{fecha.month}/"
            f"{fecha.year}"
        )

    except ValueError:
        pass

    # --------------------------------------------------------
    # DD/MM/YYYY
    # --------------------------------------------------------

    try:

        fecha = datetime.strptime(
            valor[:10],
            "%d/%m/%Y"
        )

        return (
            f"{fecha.day}/"
            f"{fecha.month}/"
            f"{fecha.year}"
        )

    except ValueError:
        pass

    return None


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

def enviar_publicacion(lanzamiento, ytmusic):

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

    fecha = obtener_fecha(
        lanzamiento,
        ytmusic
    )

    portada = obtener_imagen(
        lanzamiento
    )

    url_youtube = obtener_url_youtube_music(
        lanzamiento
    )

    # --------------------------------------------------------
    # MENSAJE
    #
    # IMPORTANTE:
    # El emoji 🎵 está DENTRO del blockquote junto al título.
    #
    # No dejamos líneas vacías entre los datos.
    # --------------------------------------------------------

    texto = (
        f"🎤 <b>{artista}</b>\n"
        f"<blockquote>🎵 <b>{titulo}</b></blockquote>\n"
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
        json=datos,
        timeout=30
    )

    print()
    print("Respuesta de Telegram:")
    print(respuesta.text)
    print()

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

        ytmusic = YTMusic()

        lanzamiento = obtener_ultimo_lanzamiento()

        enviar_publicacion(
            lanzamiento,
            ytmusic
        )

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
