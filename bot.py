import os
import json
import html
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

import requests
from ytmusicapi import YTMusic
import yt_dlp


# ============================================================
# CONFIGURACIÓN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

TELEGRAM_CHAT_ID = "@Cubaton_Music"
TELEGRAM_ALERT_CHAT_ID = "@CubatonMusicBot"

TELEGRAM_API = (
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
)


# ============================================================
# UTILIDADES
# ============================================================

def escapar(texto):
    """Escapa texto para Telegram HTML."""
    if texto is None:
        return ""
    return html.escape(str(texto))


# ============================================================
# DESCARGA DE AUDIO (CON SOPORTE DE COOKIES)
# ============================================================

def descargar_audio(youtube_url):
    """
    Descarga el audio de YouTube Music en formato MP3 
    utilizando yt-dlp y cookies locales si existen.
    """
    archivo_salida = "temp_track.mp3"

    if os.path.exists(archivo_salida):
        try:
            os.remove(archivo_salida)
        except Exception:
            pass

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'temp_track',
        'quiet': True,
        'no_warnings': True,
    }

    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        if os.path.exists(archivo_salida):
            return archivo_salida
        return None
    except Exception as error:
        print(f"Error descargando audio con yt-dlp: {error}")
        return None


# ============================================================
# ALERTAS
# ============================================================

def enviar_alerta_error(
    cancion,
    etapa,
    detalle
):
    """Envía una alerta privada cuando una publicación falla."""
    try:
        titulo = escapar(cancion.get("titulo", "Desconocido"))
        artistas = escapar(cancion.get("artistas", "Desconocido"))
        tipo = escapar(cancion.get("tipo", "Desconocido"))
        nombre_publicacion = escapar(cancion.get("nombre_publicacion", ""))
        anio = escapar(cancion.get("anio", ""))
        ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        mensaje = (
            "⚠️ <b>Error en Cubaton Music Bot (Prueba)</b>\n\n"
            f"🎤 <b>Artista(s):</b> {artistas}\n"
            f"🎵 <b>Canción:</b> {titulo}\n"
            f"📀 <b>Lanzamiento:</b> {nombre_publicacion}\n"
            f"🗓 <b>Año:</b> {anio}\n"
            f"🔧 <b>Etapa:</b> {escapar(etapa)}\n"
            f"🕐 <b>Hora:</b> {ahora}\n\n"
            f"❌ <b>Error:</b>\n{escapar(detalle)}"
        )

        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": TELEGRAM_ALERT_CHAT_ID,
                "text": mensaje,
                "parse_mode": "HTML",
            },
            timeout=30,
        )
    except Exception as error:
        print(f"No se pudo enviar la alerta de error: {error}")


# ============================================================
# PUBLICAR CANCIÓN (FLUJO SECUENCIAL FOTO + AUDIO INDEPENDIENTE)
# ============================================================

def publicar_cancion(cancion):
    """
    Publica la canción en dos mensajes secuenciales limpios:
    1. Mensaje con la foto de la portada, metadatos y botón inline.
    2. Mensaje independiente con el archivo de audio (.mp3) y etiqueta 🎧 @Cubaton_Music.
    """
    titulo = escapar(cancion["titulo"])
    artistas = escapar(cancion["artistas"])
    nombre_publicacion = escapar(cancion["nombre_publicacion"])
    anio = escapar(cancion["anio"])

    caption_foto = (
        f"🎤 <b>{artistas}</b>\n"
        f"🎵 <b>{titulo}</b>\n"
        f"📀 <b>{nombre_publicacion}</b>\n"
        f"🗓 {anio}\n\n"
        "@Cubaton_Music"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "▶️ Escuchar en YouTube Music",
                    "url": cancion["youtube_url"],
                }
            ]
        ]
    }

    thumbnails = cancion.get("thumbnails", [])
    foto_url = thumbnails[-1]["url"] if thumbnails else None

    # 1. Enviar Mensaje 1: Foto con metadatos y botón inline
    if foto_url:
        payload_foto = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": foto_url,
            "caption": caption_foto,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(reply_markup),
        }

        try:
            resp_foto = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                json=payload_foto,
                timeout=30
            )
            if not resp_foto.ok:
                return False, f"Fallo al enviar la foto: {resp_foto.text}"
            
            datos_foto = resp_foto.json()
            if not datos_foto.get("ok"):
                return False, f"Fallo al enviar la foto: {str(datos_foto)}"
        except Exception as error:
            return False, f"Excepción al enviar la foto: {str(error)}"
    else:
        return False, "No se encontró miniatura disponible para la foto."

    # 2. Descargar audio temporalmente para el Mensaje 2
    print(f"Descargando audio para: {cancion['titulo']}...")
    archivo_audio = descargar_audio(cancion["youtube_url"])

    if not archivo_audio or not os.path.exists(archivo_audio):
        return False, "Fallo al descargar el archivo de audio con yt-dlp."

    # 3. Enviar Mensaje 2: Audio independiente (sin reply) con emoji y formato requerido
    caption_audio = "🎧 @Cubaton_Music"

    try:
        with open(archivo_audio, "rb") as audio_file:
            files = {"audio": audio_file}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption_audio,
                "parse_mode": "HTML"
            }

            respuesta = requests.post(
                f"{TELEGRAM_API}/sendAudio",
                files=files,
                data=data,
                timeout=90
            )

        if os.path.exists(archivo_audio):
            os.remove(archivo_audio)

        if not respuesta.ok:
            return False, respuesta.text

        datos = respuesta.json()
        if not datos.get("ok"):
            return False, str(datos)

        return True, None

    except Exception as error:
        if os.path.exists(archivo_audio):
            os.remove(archivo_audio)
        return False, str(error)


# ============================================================
# PROGRAMA PRINCIPAL (MODO PRUEBA CON 2 URLS ESPECÍFICAS)
# ============================================================

def main():
    print("=" * 60)
    print("CUBATON MUSIC BOT - PRUEBA MANUAL")
    print("=" * 60)

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No existe el secreto TELEGRAM_BOT_TOKEN.")
        return

    enlaces_prueba = [
        "https://music.youtube.com/watch?v=AcL8k6ZyJDE&si=oCxkPYp5prlJFBbG",
        "https://music.youtube.com/watch?v=fL22w0oobqA&si=4I20UlgbuQdVhX9I",
    ]

    ytmusic = YTMusic()
    nuevas_canciones = []

    for url in enlaces_prueba:
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get("v", [None])[0]

            if not video_id:
                video_id = url.split("v=")[1].split("&")[0]

            print(f"Obteniendo metadatos para video_id: {video_id}...")
            track_info = ytmusic.get_song(video_id)
            detalles = track_info.get("videoDetails", {})
            
            titulo = detalles.get("title", "Canción de Prueba")
            autor = detalles.get("author", "Artista de Prueba")
            thumbnails = detalles.get("thumbnail", {}).get("thumbnails", [])

            cancion = {
                "id": f"video:{video_id}",
                "video_id": video_id,
                "titulo": titulo,
                "artistas": autor,
                "tipo": "Single",
                "anio": "2026",
                "nombre_publicacion": "Single",
                "youtube_url": url,
                "thumbnails": thumbnails,
            }
            nuevas_canciones.append(cancion)
        except Exception as error:
            print(f"Error procesando el enlace {url}: {error}")

    if not nuevas_canciones:
        print("No se pudieron cargar las canciones de prueba.")
        return

    print(f"\nIniciando prueba con {len(nuevas_canciones)} canción(es).\n")

    publicadas = 0
    errores = 0

    for numero, cancion in enumerate(nuevas_canciones, start=1):
        print(f"[PRUEBA {numero}/{len(nuevas_canciones)}]")
        print(f"Artista(s): {cancion['artistas']}")
        print(f"Canción: {cancion['titulo']}")

        exito, error = publicar_cancion(cancion)

        if exito:
            print("¡PUBLICADO CORRECTAMENTE EN TELEGRAM!\n")
            publicadas += 1
        else:
            print(f"ERROR AL PUBLICAR: {error}\n")
            errores += 1
            enviar_alerta_error(cancion, "Prueba Manual en Telegram", error)

        print()

    print("=" * 60)
    print("RESUMEN DE LA PRUEBA")
    print(f"Total procesadas: {len(nuevas_canciones)}")
    print(f"Publicadas con éxito: {publicadas}")
    print(f"Errores: {errores}")
    print("=" * 60)


if __name__ == "__main__":
    main()
