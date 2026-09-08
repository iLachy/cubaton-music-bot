import os
import json
import html
import io
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

import requests
from ytmusicapi import YTMusic
import yt_dlp
from PIL import Image


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
# UTILIDADES Y VERIFICACIONES
# ============================================================

def escapar(texto):
    """Escapa texto para Telegram HTML."""
    if texto is None:
        return ""
    return html.escape(str(texto))

def verificar_ffmpeg():
    """Comprueba si FFmpeg está instalado y accesible en el sistema."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            check=True
        )
        return True
    except Exception:
        return False

def preparar_miniatura(url_imagen, archivo_salida="temp_thumb.jpg"):
    """
    Descarga la miniatura, la recorta a formato cuadrado (1:1) 
    eliminando los espacios vacíos laterales y la guarda localmente.
    """
    if os.path.exists(archivo_salida):
        try:
            os.remove(archivo_salida)
        except Exception:
            pass

    try:
        resp = requests.get(url_imagen, timeout=20)
        if not resp.ok:
            return None
        
        img = Image.open(io.BytesIO(resp.content))
        ancho, alto = img.size

        # Si la imagen es más ancha que alta, recortamos los laterales simétricamente
        if ancho > alto:
            diferencia = ancho - alto
            inicio_x = diferencia // 2
            fin_x = inicio_x + alto
            img = img.crop((inicio_x, 0, fin_x, alto))

        img.save(archivo_salida, "JPEG")
        if os.path.exists(archivo_salida):
            return archivo_salida
        return None
    except Exception as error:
        print(f"Error procesando miniatura: {error}")
        return None


# ============================================================
# DESCARGA DE AUDIO (CON CONVERSIÓN DE URL Y BYPASS)
# ============================================================

def descargar_audio(video_id):
    """
    Descarga el audio en formato MP3 utilizando yt-dlp.
    Usa el enlace estándar de YouTube (no music) para evitar el error de formatos ocultos.
    """
    archivo_salida = "temp_track.mp3"
    url_descarga = f"https://www.youtube.com/watch?v={video_id}"

    if os.path.exists(archivo_salida):
        try:
            os.remove(archivo_salida)
        except Exception:
            pass

    ydl_opts = {
        'format': 'ba/b', # Best audio o Best fallback
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'temp_track',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'default']
            }
        },
    }

    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_descarga])

        if os.path.exists(archivo_salida):
            return archivo_salida
        return None
    except Exception as error:
        print(f"Error descargando audio con yt-dlp: {error}")
        return None


# ============================================================
# ALERTAS
# ============================================================

def enviar_alerta_error(cancion, etapa, detalle):
    """Envía una alerta privada cuando una publicación falla."""
    try:
        titulo = escapar(cancion.get("titulo", "Desconocido"))
        artistas = escapar(cancion.get("artistas", "Desconocido"))
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
    1. Mensaje con la foto de portada recortada (cuadrada), metadatos y botón inline.
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

    if not foto_url:
        return False, "No se encontró miniatura disponible para la foto."

    # Procesar y recortar la miniatura
    print(f"Procesando y recortando miniatura para: {cancion['titulo']}...")
    archivo_foto_local = preparar_miniatura(foto_url)

    if not archivo_foto_local or not os.path.exists(archivo_foto_local):
        return False, "Fallo al procesar/recortar la miniatura de la foto."

    # 1. Enviar Mensaje 1: Foto recortada
    try:
        with open(archivo_foto_local, "rb") as foto_file:
            files = {"photo": foto_file}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption_foto,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(reply_markup),
            }

            resp_foto = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                files=files,
                data=data,
                timeout=45
            )

        if os.path.exists(archivo_foto_local):
            os.remove(archivo_foto_local)

        if not resp_foto.ok:
            return False, f"Fallo al enviar la foto: {resp_foto.text}"
        
        datos_foto = resp_foto.json()
        if not datos_foto.get("ok"):
            return False, f"Fallo al enviar la foto: {str(datos_foto)}"
    except Exception as error:
        if os.path.exists(archivo_foto_local):
            os.remove(archivo_foto_local)
        return False, f"Excepción al enviar la foto: {str(error)}"

    # 2. Descargar audio
    print(f"Descargando audio para: {cancion['titulo']}...")
    archivo_audio = descargar_audio(cancion["video_id"])

    if not archivo_audio or not os.path.exists(archivo_audio):
        return False, "Fallo al descargar el archivo de audio con yt-dlp."

    # 3. Enviar Mensaje 2: Audio independiente
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
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("=" * 60)
    print("CUBATON MUSIC BOT - PRUEBA MANUAL")
    print("=" * 60)

    # --------------------------------------------------------
    # NUEVO: Verificación de FFmpeg al inicio del script
    # --------------------------------------------------------
    if verificar_ffmpeg():
        print("✅ FFmpeg está instalado correctamente y listo para convertir audio.\n")
    else:
        print("❌ ADVERTENCIA: FFmpeg NO está instalado o no está en el PATH.\n")
    # --------------------------------------------------------

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

            print(f"Obteniendo metadatos reales para video_id: {video_id}...")
            
            watch_info = ytmusic.get_watch_playlist(videoId=video_id)
            song_info = ytmusic.get_song(video_id)
            
            track_data = watch_info["tracks"][0] if watch_info.get("tracks") else {}
            video_details = song_info.get("videoDetails", {})
            
            titulo = track_data.get("title") or video_details.get("title", "Canción Desconocida")
            
            artistas_raw = track_data.get("artists", [])
            if artistas_raw:
                autor = ", ".join([a["name"] for a in artistas_raw if "name" in a and a["name"] != "Topic"])
            else:
                autor = video_details.get("author", "Artista Desconocido").replace(" - Topic", "")
            
            album_info = track_data.get("album")
            nombre_publicacion = album_info.get("name") if album_info else "Single"
            
            anio = datetime.now().year
            try:
                publish_date = song_info.get("microformat", {}).get("microformatDataRenderer", {}).get("publishDate", "")
                if publish_date:
                    anio = publish_date.split("-")[0]
            except Exception:
                pass
            
            thumbnails = track_data.get("thumbnail", [])
            if not thumbnails:
                thumbnails = video_details.get("thumbnail", {}).get("thumbnails", [])
            if not thumbnails:
                thumbnails = [{"url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"}]

            cancion = {
                "id": f"video:{video_id}",
                "video_id": video_id,
                "titulo": titulo,
                "artistas": autor,
                "tipo": "Lanzamiento",
                "anio": str(anio),
                "nombre_publicacion": nombre_publicacion,
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
        print(f"Álbum/Lanzamiento: {cancion['nombre_publicacion']}")
        print(f"Año: {cancion['anio']}")

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
