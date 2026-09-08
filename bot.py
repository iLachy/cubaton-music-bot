import os
import json
import html
from datetime import datetime, timezone
import requests
from ytmusicapi import YTMusic
import yt_dlp  # NUEVO IMPORT PARA DESCARGAR AUDIO

# ============================================================
# CONFIGURACIÓN
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@Cubaton_Music"
TELEGRAM_ALERT_CHAT_ID = "@CubatonMusicBot"
STATE_FILE = "state/releases.json"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ============================================================
# ARTISTAS MONITORIZADOS (Mantenemos tu lista intacta)
# ============================================================
ARTISTAS = [
    {
        "nombre": "Bebeshito",
        "channel_id": "UCpVfWS-cPOE2sYqsFuuP_Qg",
    },
    {
        "nombre": "Charly & Johayron",
        "channel_id": "UCnwEtOQyXJUUuBhcTgImdfQ",
    },
    {
        "nombre": "Dany Ome",
        "channel_id": "UCJQEm9t4KjDn-I8Fahf4Uqw",
    },
    {
        "nombre": "Wampi",
        "channel_id": "UCbfzw8u1lCwDMv443StJEOw",
    },
    {
        "nombre": "El Taiger",
        "channel_id": "UCoYtt7bGCV5RyUweyQgqQ4A",
    },
    {
        "nombre": "Ja Rulay",
        "channel_id": "UCcaU4COep7mj8kbXwS24JFQ",
    },
    {
        "nombre": "L Kimii",
        "channel_id": "UCMyQosiL8iVUtXPIm1UZJQg",
    },
    {
        "nombre": "El Dray",
        "channel_id": "UC4kpn8y8QXYXmyDn8HJKD8Q",
    },
    {
        "nombre": "Mauro y El Pitu",
        "channel_id": "UCvN1mRFfAfWYTiIkM70qUWA",
    },
    {
        "nombre": "Yirow Y El Tingo",
        "channel_id": "UCEq3_5h1Xi_vLbytP7OzuNA",
    },
    {
        "nombre": "Nany La Kbra",
        "channel_id": "UCG4lSNdNx_LuLnN2EW6uWwQ",
    },
    {
        "nombre": "Ya Ice Dilan",
        "channel_id": "UC9aJbR9Q8nscvZaMw_cH4Ww",
    },
    {
        "nombre": "Rey Tony",
        "channel_id": "UCDhExL0uVtumv_DEjPPq5qg",
    },
    {
        "nombre": "Baby Maikol",
        "channel_id": "UCP5R6Mgbk_bgtgzZguLNKdA",
    },
    {
        "nombre": "Payaso X Ley",
        "channel_id": "UCauTaqBvFqqqJTu3B4Wc1GA",
    },
    {
        "nombre": "Kaly Y Kowa",
        "channel_id": "UCSfR51myQhs2ZcdzrWo0Z4w",
    },
    {
        "nombre": "Wildey",
        "channel_id": "UCmFS-VSa4Wf3F1wdWS-8p_g",
    },
    {
        "nombre": "Wow Popy",
        "channel_id": "UCtFkN8UFxT_MuNdySlfuFuA",
    },
    {
        "nombre": "Talent Fuego",
        "channel_id": "UC0dVmcXfNa7lVeUBve3_FXw",
    },
    {
        "nombre": "Mawell",
        "channel_id": "UCL6P-jUDZEKBA-Lb6WFccWg",
    },
    {
        "nombre": "Harryson",
        "channel_id": "UC2ihX5uoblnN4wsA-ayIAAA",
    },
    {
        "nombre": "El Chulo",
        "channel_id": "UCiT8VNdnpeYnCTPJZoqym9g",
    },
    {
        "nombre": "Fixty Ordara",
        "channel_id": "UCDHDCbVOQywsLCsCZ8PH-AA",
    },
    {
        "nombre": "El Kamel",
        "channel_id": "UCPnWcazEV7QM0H7qBx6NVXg",
    },
    {
        "nombre": "Velito el Bufón",
        "channel_id": "UCRA9cRfAJXuxDRcFnoB7pwg",
    },
    {
        "nombre": "Un Titico",
        "channel_id": "UCT2KiGFSPZIF3DR9UIN2fYw",
    },
    {
        "nombre": "Musteerifa",
        "channel_id": "UCiT8PzlQqtPC7lWFh3--4jw",
    },
    {
        "nombre": "Chocolate MC",
        "channel_id": "UCYVuThmAmbXxk1o9Un5Cc_w",
    },
    {
        "nombre": "El Chacal",
        "channel_id": "UCJt4IsSmUjqTaamhCJoKK_g",
    },
    {
        "nombre": "El Micha",
        "channel_id": "UCHhrMSqe_C1E_JBEz3mRlew",
    },
    {
        "nombre": "Yomil",
        "channel_id": "UCPfXwOpwRIbVsqqTsgt4i5g",
    },
    {
        "nombre": "Jacob Forever",
        "channel_id": "UCJ1-Pwsroy-gzMqlfKDF4Hg",
    },
    {
        "nombre": "Gente de Zona",
        "channel_id": "UCl2KQVc_GFH081i7b9CJQug",
    },
    {
        "nombre": "La Diosa",
        "channel_id": "UChbVOQHgq01JoHY4axuWV0A",
    },
    {
        "nombre": "Seidy La Niña",
        "channel_id": "UCFqYfgj_7h3ZUkBnyYS-TFg",
    },
]


# ============================================================
# UTILIDADES
# ============================================================
def escapar(texto):
    """Escapa texto para Telegram HTML."""
    if texto is None:
        return ""
    return html.escape(str(texto))


def normalizar_nombre(nombre):
    """Normaliza un nombre para comparaciones."""
    return " ".join(str(nombre).strip().split()).casefold()


# ============================================================
# ESTADO
# ============================================================
ESTADO_VERSION = 2


def cargar_estado():
    """Carga el estado. La versión 2 guarda cada canción individualmente."""
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as archivo:
            estado = json.load(archivo)
        if not isinstance(estado, dict):
            return None
        if estado.get("version") != ESTADO_VERSION:
            return None
        canciones = estado.get("canciones", [])
        if not isinstance(canciones, list):
            return None
        return {
            "version": ESTADO_VERSION,
            "canciones": set(canciones),
        }
    except Exception as error:
        print(f"No se pudo cargar el estado: {error}")
        return None


def guardar_estado(estado):
    """Guarda el estado en state/releases.json."""
    carpeta = os.path.dirname(STATE_FILE)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    datos = {
        "version": ESTADO_VERSION,
        "canciones": sorted(list(estado["canciones"])),
    }
    with open(STATE_FILE, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


# ============================================================
# ARTISTAS
# ============================================================
def formatear_artistas(artistas):
    """Formatea los artistas acreditados."""
    nombres = []
    vistos = set()
    for artista in artistas:
        if not artista:
            continue
        nombre = str(artista).strip()
        if not nombre:
            continue
        clave = normalizar_nombre(nombre)
        if clave in vistos:
            continue
        vistos.add(clave)
        nombres.append(nombre)
    return ", ".join(nombres)


def extraer_artistas_de_objetos(objetos):
    """Extrae nombres de artistas."""
    resultado = []
    if not objetos:
        return resultado
    for artista in objetos:
        if not isinstance(artista, dict):
            continue
        nombre = artista.get("name")
        if nombre:
            resultado.append(nombre)
    return resultado


# ============================================================
# INFORMACIÓN DEL ÁLBUM / EP
# ============================================================
def obtener_datos_album(ytmusic, browse_id):
    """Obtiene información completa de un EP o álbum."""
    if not browse_id:
        return None
    try:
        return ytmusic.get_album(browse_id)
    except Exception as error:
        print(f"No se pudo obtener el álbum {browse_id}: {error}")
        return None


# ============================================================
# CREAR CANCIÓN
# ============================================================
def crear_cancion_desde_track(
    track,
    artista_principal,
    tipo_lanzamiento,
    anio,
    titulo_lanzamiento=None,
    album_browse_id=None,
):
    """Convierte una pista de YouTube Music en una canción individual."""
    if not isinstance(track, dict):
        return None
    video_id = track.get("videoId")
    if not video_id:
        return None
    titulo = track.get("title")
    if not titulo:
        return None
    artistas = extraer_artistas_de_objetos(track.get("artists"))
    if not artistas:
        artistas = [artista_principal]
    artistas_formateados = formatear_artistas(artistas)
    if tipo_lanzamiento == "Single":
        nombre_publicacion = "Single"
    else:
        nombre_publicacion = titulo_lanzamiento or "Sin título"
    youtube_url = f"https://music.youtube.com/watch?v={video_id}"
    return {
        "id": f"video:{video_id}",
        "video_id": video_id,
        "titulo": titulo,
        "artistas": artistas_formateados,
        "tipo": tipo_lanzamiento,
        "anio": str(anio or ""),
        "nombre_publicacion": nombre_publicacion,
        "youtube_url": youtube_url,
        "artista_monitorizado": artista_principal,
        "titulo_lanzamiento": titulo_lanzamiento or titulo,
        "album_browse_id": album_browse_id,
    }


# ============================================================
# OBTENER CANCIONES DE UN ARTISTA
# ============================================================
def obtener_lanzamientos_artista(ytmusic, artista):
    """Obtiene canciones individuales de un artista."""
    nombre = artista["nombre"]
    channel_id = artista["channel_id"]
    try:
        datos = ytmusic.get_artist(channel_id)
    except Exception as error:
        return []
    canciones = []

    # Singles
    singles = datos.get("singles", {})
    for single in singles.get("results", []):
        video_id = single.get("videoId")
        if not video_id:
            continue
        titulo = single.get("title")
        if not titulo:
            continue
        artistas = extraer_artistas_de_objetos(single.get("artists"))
        if not artistas:
            artistas = [nombre]
        anio = single.get("year", "")
        cancion = crear_cancion_desde_track(
            {
                "videoId": video_id,
                "title": titulo,
                "artists": [{"name": a} for a in artistas],
            },
            nombre,
            "Single",
            anio,
            titulo_lanzamiento=titulo,
        )
        if cancion:
            canciones.append(cancion)

    # Álbumes / EPs
    albums = datos.get("albums", {})
    for album in albums.get("results", []):
        browse_id = album.get("browseId")
        if not browse_id:
            continue
        titulo_album = album.get("title", "Sin título")
        tipo_album = album.get("type", "Album")
        tipo_normalizado = str(tipo_album).strip()
        if tipo_normalizado.casefold() == "ep":
            tipo_normalizado = "EP"
        elif tipo_normalizado.casefold() in ("album", "álbum"):
            tipo_normalizado = "Album"
        anio = album.get("year", "")
        datos_album = obtener_datos_album(ytmusic, browse_id)
        if not datos_album:
            continue
        tipo_datos = datos_album.get("type")
        if tipo_datos:
            tipo_normalizado = str(tipo_datos).strip()
            if tipo_normalizado.casefold() == "ep":
                tipo_normalizado = "EP"
            elif tipo_normalizado.casefold() in ("album", "álbum"):
                tipo_normalizado = "Album"
        anio_datos = datos_album.get("year")
        if anio_datos:
            anio = anio_datos
        tracks = datos_album.get("tracks", [])
        for track in tracks:
            cancion = crear_cancion_desde_track(
                track,
                nombre,
                tipo_normalizado,
                anio,
                titulo_lanzamiento=titulo_album,
                album_browse_id=browse_id,
            )
            if cancion:
                canciones.append(cancion)
    return canciones


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
            "⚠️ <b>Error en Cubaton Music Bot</b>\n\n"
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
# PUBLICAR CANCIÓN (Mensaje 1: Foto con Metadatos)
# ============================================================
def publicar_cancion(cancion):
    titulo = escapar(cancion["titulo"])
    artistas = escapar(cancion["artistas"])
    nombre_publicacion = escapar(cancion["nombre_publicacion"])
    anio = escapar(cancion["anio"])

    caption = (
        f"🎤 <b>{artistas}</b>\n"
        f"🎵 <b>{titulo}</b>\n"
        f"📀 <b>{nombre_publicacion}</b>\n"
        f"🗓 {anio}"
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

    video_id = cancion["video_id"]
    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": thumbnail_url,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": reply_markup,
    }

    try:
        respuesta = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            json=payload,
            timeout=30,
        )
        if not respuesta.ok:
            return (False, respuesta.text)
        datos = respuesta.json()
        if not datos.get("ok"):
            return (False, str(datos))
        return (True, None)
    except Exception as error:
        return (False, str(error))


# ============================================================
# DESCARGAR Y PUBLICAR AUDIO (Mensaje 2: Archivo MP3)
# ============================================================
def descargar_y_enviar_audio(cancion):
    video_id = cancion["video_id"]
    url = cancion["youtube_url"]
    archivo_temporal = f"{video_id}.m4a"

    print("   ⬇️ Descargando audio desde YouTube Music...")

    ydl_opts = {
        "format": "ba[ext=m4a]/ba[ext=mp3]/ba",
        "outtmpl": archivo_temporal,
        "quiet": True,
        "no_warnings": True,
        "extract_audio": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(archivo_temporal):
            return (False, "El archivo de audio no se generó correctamente.")

        print("   ⬆️ Subiendo audio a Telegram...")

        with open(archivo_temporal, "rb") as audio_file:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": "🎧 @Cubaton_Music",
                "title": cancion["titulo"],
                "performer": cancion["artistas"],
            }
            archivos = {"audio": audio_file}

            respuesta = requests.post(
                f"{TELEGRAM_API}/sendAudio",
                data=payload,
                files=archivos,
                timeout=120,
            )

            if not respuesta.ok:
                return (False, respuesta.text)

            datos = respuesta.json()
            if not datos.get("ok"):
                return (False, str(datos))

        return (True, None)

    except Exception as error:
        return (False, str(error))
    finally:
        if os.path.exists(archivo_temporal):
            os.remove(archivo_temporal)


# ============================================================
# PROGRAMA PRINCIPAL (MODIFICADO PARA PRUEBA DE 2 URLS EXACTAS)
# ============================================================
def main():
    print("=" * 60)
    print("CUBATON MUSIC BOT - MODO PRUEBA MANUAL")
    print("=" * 60)

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No existe el secreto TELEGRAM_BOT_TOKEN.")
        return

    ytmusic = YTMusic()

    # URLs de prueba proporcionadas
    urls_prueba = [
        "https://music.youtube.com/watch?v=a6W8HbHtP54",
        "https://music.youtube.com/watch?v=OpY_ZT4vCAc",
    ]

    nuevas_canciones = []

    for url in urls_prueba:
        try:
            video_id = url.split("v=")[1].split("&")[0]
            info = ytmusic.get_song(video_id)
            detalles = info.get("videoDetails", {})

            titulo = detalles.get("title", "Desconocido")
            autor = detalles.get("author", "Artista Cubano")
            anio = "2026"  # Año por defecto para la prueba

            cancion = {
                "id": f"video:{video_id}",
                "video_id": video_id,
                "titulo": titulo,
                "artistas": autor,
                "tipo": "Single",
                "anio": anio,
                "nombre_publicacion": "Single",
                "youtube_url": url,
            }
            nuevas_canciones.append(cancion)
            print(f"✅ Canción cargada para prueba: {autor} - {titulo}")
        except Exception as e:
            print(f"❌ No se pudo procesar la URL {url}: {e}")

    if not nuevas_canciones:
        print("No hay canciones para probar.")
        return

    print(f"\nIniciando publicación de prueba de {len(nuevas_canciones)} canciones...\n")

    for numero, cancion in enumerate(nuevas_canciones, start=1):
        print(f"[PUBLICACIÓN {numero}/{len(nuevas_canciones)}]")
        print(f"Artista(s): {cancion['artistas']}")
        print(f"Canción: {cancion['titulo']}")

        # 1. Enviar Imagen con Metadatos
        exito_foto, error_foto = publicar_cancion(cancion)

        if exito_foto:
            print("   ✅ METADATOS PUBLICADOS")

            # 2. Descargar y Enviar Audio
            exito_audio, error_audio = descargar_y_enviar_audio(cancion)

            if exito_audio:
                print("   ✅ AUDIO PUBLICADO CORRECTAMENTE\n")
            else:
                print("   ❌ ERROR AL PUBLICAR AUDIO")
                print(error_audio)
                enviar_alerta_error(cancion, "Subida de Audio Prueba", error_audio)
                print()
        else:
            print("   ❌ ERROR AL PUBLICAR METADATOS")
            print(error_foto)
            enviar_alerta_error(cancion, "Publicación Metadatos Prueba", error_foto)
            print()

    print("=" * 60)
    print("PRUEBA FINALIZADA")
    print("=" * 60)


if __name__ == "__main__":
    main()
