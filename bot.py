import os
import json
import html
from datetime import datetime, timezone

import requests
from ytmusicapi import YTMusic
import yt_dlp


# ============================================================
# CONFIGURACIÓN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

TELEGRAM_CHAT_ID = "@Cubaton_Music"
TELEGRAM_ALERT_CHAT_ID = "@CubatonMusicBot"

STATE_FILE = "state/releases.json"

TELEGRAM_API = (
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
)


# ============================================================
# ARTISTAS MONITORIZADOS
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
    return " ".join(
        str(nombre).strip().split()
    ).casefold()


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
# ESTADO
# ============================================================

ESTADO_VERSION = 2


def cargar_estado():
    """Carga el estado."""

    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:

            estado = json.load(archivo)

        if not isinstance(estado, dict):
            return None

        if estado.get("version") != ESTADO_VERSION:
            print("Estado antiguo detectado.")
            print(
                "Se reconstruirá la línea base "
                "con el nuevo sistema."
            )
            return None

        canciones = estado.get(
            "canciones",
            []
        )

        if not isinstance(canciones, list):
            return None

        return {
            "version": ESTADO_VERSION,
            "canciones": set(canciones),
        }

    except Exception as error:

        print(
            f"No se pudo cargar el estado: {error}"
        )

        return None


def guardar_estado(estado):
    """Guarda el estado en state/releases.json."""

    carpeta = os.path.dirname(STATE_FILE)

    if carpeta:
        os.makedirs(
            carpeta,
            exist_ok=True
        )

    datos = {
        "version": ESTADO_VERSION,
        "canciones": sorted(
            list(estado["canciones"])
        ),
    }

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2
        )


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

        nombre = str(
            artista
        ).strip()

        if not nombre:
            continue

        clave = normalizar_nombre(
            nombre
        )

        if clave in vistos:
            continue

        vistos.add(clave)
        nombres.append(nombre)

    claves = {
        normalizar_nombre(nombre)
        for nombre in nombres
    }

    tiene_rey_tony = (
        "rey tony" in claves
    )

    tiene_helabusador = (
        "helabusador" in claves
    )

    if (
        tiene_rey_tony
        and tiene_helabusador
    ):

        resultado = []

        for nombre in nombres:

            clave = normalizar_nombre(
                nombre
            )

            if clave in (
                "rey tony",
                "helabusador",
            ):
                continue

            resultado.append(nombre)

        resultado.insert(
            0,
            "Rey Tony & Helabusador"
        )

        nombres = resultado

    return ", ".join(nombres)


def extraer_artistas_de_objetos(objetos):
    """Extrae nombres de artistas."""
    resultado = []

    if not objetos:
        return resultado

    for artista in objetos:

        if not isinstance(
            artista,
            dict
        ):
            continue

        nombre = artista.get(
            "name"
        )

        if nombre:
            resultado.append(
                nombre
            )

    return resultado


# ============================================================
# INFORMACIÓN DEL ÁLBUM / EP
# ============================================================

def obtener_datos_album(
    ytmusic,
    browse_id
):
    """Obtiene información completa de un EP o álbum."""
    if not browse_id:
        return None

    try:

        return ytmusic.get_album(
            browse_id
        )

    except Exception as error:

        print(
            f"No se pudo obtener "
            f"el álbum {browse_id}: "
            f"{error}"
        )

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
    album_thumbnails=None,
):
    """Convierte una pista de YouTube Music en una canción individual."""
    if not isinstance(
        track,
        dict
    ):
        return None

    video_id = track.get(
        "videoId"
    )

    if not video_id:
        return None

    titulo = track.get(
        "title"
    )

    if not titulo:
        return None

    artistas = (
        extraer_artistas_de_objetos(
            track.get("artists")
        )
    )

    if not artistas:
        artistas = [
            artista_principal
        ]

    artistas_formateados = (
        formatear_artistas(
            artistas
        )
    )

    if tipo_lanzamiento == "Single":

        nombre_publicacion = "Single"

    else:

        nombre_publicacion = (
            titulo_lanzamiento
            or "Sin título"
        )

    youtube_url = (
        "https://music.youtube.com/"
        f"watch?v={video_id}"
    )

    thumbnails = (
        track.get("thumbnails")
        or album_thumbnails
        or []
    )

    return {

        "id": f"video:{video_id}",

        "video_id": video_id,

        "titulo": titulo,

        "artistas": (
            artistas_formateados
        ),

        "tipo": tipo_lanzamiento,

        "anio": str(
            anio or ""
        ),

        "nombre_publicacion": (
            nombre_publicacion
        ),

        "youtube_url": youtube_url,

        "artista_monitorizado": (
            artista_principal
        ),

        "titulo_lanzamiento": (
            titulo_lanzamiento
            or titulo
        ),

        "album_browse_id": (
            album_browse_id
        ),

        "thumbnails": thumbnails,
    }


# ============================================================
# OBTENER CANCIONES DE UN ARTISTA
# ============================================================

def obtener_lanzamientos_artista(
    ytmusic,
    artista
):
    """Obtiene canciones individuales de singles, EPs y álbumes."""
    nombre = artista["nombre"]

    channel_id = artista[
        "channel_id"
    ]

    print(
        f"Comprobando: {nombre}"
    )

    try:

        datos = ytmusic.get_artist(
            channel_id
        )

    except Exception as error:

        print(
            f"ERROR obteniendo "
            f"artista {nombre}: "
            f"{error}"
        )

        return []

    canciones = []

    # SINGLES
    singles = datos.get(
        "singles",
        {}
    )

    resultados_singles = (
        singles.get(
            "results",
            []
        )
    )

    for single in resultados_singles:

        video_id = single.get(
            "videoId"
        )

        if not video_id:
            continue

        titulo = single.get(
            "title"
        )

        if not titulo:
            continue

        artistas = (
            extraer_artistas_de_objetos(
                single.get(
                    "artists"
                )
            )
        )

        if not artistas:
            artistas = [
                nombre
            ]

        anio = single.get(
            "year",
            ""
        )

        single_thumbnails = single.get(
            "thumbnails",
            []
        )

        cancion = (
            crear_cancion_desde_track(
                {
                    "videoId": video_id,
                    "title": titulo,
                    "artists": [
                        {
                            "name":
                            artista_nombre
                        }
                        for artista_nombre
                        in artistas
                    ],
                    "thumbnails": single_thumbnails,
                },
                nombre,
                "Single",
                anio,
                titulo_lanzamiento=titulo,
            )
        )

        if cancion:
            canciones.append(
                cancion
            )

    # EP / ÁLBUMES
    albums = datos.get(
        "albums",
        {}
    )

    resultados_albums = (
        albums.get(
            "results",
            []
        )
    )

    for album in resultados_albums:

        browse_id = album.get(
            "browseId"
        )

        if not browse_id:
            continue

        titulo_album = album.get(
            "title",
            "Sin título"
        )

        tipo_album = album.get(
            "type",
            "Album"
        )

        tipo_normalizado = str(
            tipo_album
        ).strip()

        if (
            tipo_normalizado.casefold()
            == "ep"
        ):

            tipo_normalizado = "EP"

        elif (
            tipo_normalizado.casefold()
            in ("album", "álbum")
        ):

            tipo_normalizado = "Album"

        anio = album.get(
            "year",
            ""
        )

        album_thumbnails = album.get(
            "thumbnails",
            []
        )

        datos_album = (
            obtener_datos_album(
                ytmusic,
                browse_id
            )
        )

        if not datos_album:
            continue

        if not album_thumbnails:
            album_thumbnails = datos_album.get(
                "thumbnails",
                []
            )

        tipo_datos = (
            datos_album.get(
                "type"
            )
        )

        if tipo_datos:

            tipo_normalizado = str(
                tipo_datos
            ).strip()

            if (
                tipo_normalizado.casefold()
                == "ep"
            ):

                tipo_normalizado = "EP"

            elif (
                tipo_normalizado.casefold()
                in ("album", "álbum")
            ):

                tipo_normalizado = "Album"

        anio_datos = (
            datos_album.get(
                "year"
            )
        )

        if anio_datos:
            anio = anio_datos

        tracks = (
            datos_album.get(
                "tracks",
                []
            )
        )

        if not tracks:
            continue

        for track in tracks:

            cancion = (
                crear_cancion_desde_track(
                    track,
                    nombre,
                    tipo_normalizado,
                    anio,
                    titulo_lanzamiento=(
                        titulo_album
                    ),
                    album_browse_id=(
                        browse_id
                    ),
                    album_thumbnails=(
                        album_thumbnails
                    ),
                )
            )

            if cancion:
                canciones.append(
                    cancion
                )

    return canciones


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

        titulo = escapar(
            cancion.get(
                "titulo",
                "Desconocido"
            )
        )

        artistas = escapar(
            cancion.get(
                "artistas",
                "Desconocido"
            )
        )

        tipo = escapar(
            cancion.get(
                "tipo",
                "Desconocido"
            )
        )

        nombre_publicacion = (
            cancion.get(
                "nombre_publicacion",
                ""
            )
        )

        nombre_publicacion = escapar(
            nombre_publicacion
        )

        anio = escapar(
            cancion.get(
                "anio",
                ""
            )
        )

        ahora = (
            datetime.now(
                timezone.utc
            ).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        )

        mensaje = (
            "⚠️ <b>Error en "
            "Cubaton Music Bot</b>\n\n"

            f"🎤 <b>Artista(s):</b> "
            f"{artistas}\n"

            f"🎵 <b>Canción:</b> "
            f"{titulo}\n"

            f"📀 <b>Lanzamiento:</b> "
            f"{nombre_publicacion}\n"

            f"🗓 <b>Año:</b> "
            f"{anio}\n"

            f"🔧 <b>Etapa:</b> "
            f"{escapar(etapa)}\n"

            f"🕐 <b>Hora:</b> "
            f"{ahora}\n\n"

            f"❌ <b>Error:</b>\n"
            f"{escapar(detalle)}\n\n"

            "🔄 La canción NO se marcará "
            "como publicada y será "
            "intentada nuevamente "
            "en la próxima ejecución."
        )

        respuesta = requests.post(

            f"{TELEGRAM_API}/sendMessage",

            json={
                "chat_id":
                    TELEGRAM_ALERT_CHAT_ID,

                "text":
                    mensaje,

                "parse_mode":
                    "HTML",
            },

            timeout=30,
        )

        if not respuesta.ok:

            print(
                "No se pudo enviar "
                "la alerta de Telegram: "
                f"{respuesta.text}"
            )

    except Exception as error:

        print(
            "No se pudo enviar "
            f"la alerta de error: {error}"
        )


# ============================================================
# PUBLICAR CANCIÓN (FLUJO SECUENCIAL FOTO + AUDIO INDEPENDIENTE)
# ============================================================

def publicar_cancion(
    cancion
):
    """
    Publica la canción en dos mensajes secuenciales limpios:
    1. Mensaje con la foto de la portada, metadatos y botón inline.
    2. Mensaje independiente con el archivo de audio (.mp3) y etiqueta 🎧 @Cubaton_Music.
    """
    titulo = escapar(
        cancion["titulo"]
    )

    artistas = escapar(
        cancion["artistas"]
    )

    nombre_publicacion = escapar(
        cancion[
            "nombre_publicacion"
        ]
    )

    anio = escapar(
        cancion["anio"]
    )

    caption_foto = (
        f"🎤 <b>{artistas}</b>\n"
        f"🎵 <b>{titulo}</b>\n"
        f"📀 <b>{nombre_publicacion}</b>\n"
        f"🗓 {anio}\n"
        f"\n"
        f"@Cubaton_Music"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text":
                        "▶️ Escuchar en YouTube Music",

                    "url":
                        cancion[
                            "youtube_url"
                        ],
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
            files = {
                "audio": audio_file
            }
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
# CREAR LÍNEA BASE
# ============================================================

def crear_linea_base(
    ytmusic
):
    """Crea la línea base del nuevo sistema sin publicar nada."""
    print()
    print(
        "CREANDO NUEVA LÍNEA BASE"
    )

    canciones_registradas = set()
    total_canciones = 0

    for numero, artista in enumerate(
        ARTISTAS,
        start=1
    ):

        print(
            f"[{numero}/{len(ARTISTAS)}] "
            f"Comprobando: "
            f"{artista['nombre']}"
        )

        canciones = (
            obtener_lanzamientos_artista(
                ytmusic,
                artista
            )
        )

        for cancion in canciones:

            cancion_id = cancion[
                "id"
            ]

            if (
                cancion_id
                in canciones_registradas
            ):
                continue

            canciones_registradas.add(
                cancion_id
            )

            total_canciones += 1

    estado = {

        "version":
            ESTADO_VERSION,

        "canciones":
            canciones_registradas,
    }

    guardar_estado(
        estado
    )

    print()
    print("=" * 60)
    print("LÍNEA BASE CREADA CORRECTAMENTE")
    print(f"Canciones registradas: {total_canciones}")
    print("=" * 60)

    return estado


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print("=" * 60)
    print("CUBATON MUSIC BOT")
    print("=" * 60)

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No existe el secreto TELEGRAM_BOT_TOKEN.")
        return

    ytmusic = YTMusic()

    estado = cargar_estado()

    if estado is None:
        crear_linea_base(
            ytmusic
        )
        return

    canciones_publicadas = (
        estado[
            "canciones"
        ]
    )

    print(f"Canciones registradas actualmente: {len(canciones_publicadas)}\n")

    nuevas_canciones = []
    detectadas_en_esta_ejecucion = set()

    for numero, artista in enumerate(
        ARTISTAS,
        start=1
    ):

        print(
            f"[{numero}/{len(ARTISTAS)}] "
            f"Comprobando: "
            f"{artista['nombre']}"
        )

        canciones = (
            obtener_lanzamientos_artista(
                ytmusic,
                artista
            )
        )

        for cancion in canciones:

            cancion_id = cancion[
                "id"
            ]

            if (
                cancion_id
                in canciones_publicadas
            ):
                continue

            if (
                cancion_id
                in detectadas_en_esta_ejecucion
            ):
                continue

            detectadas_en_esta_ejecucion.add(
                cancion_id
            )

            nuevas_canciones.append(
                cancion
            )

    print()

    if not nuevas_canciones:
        print("No se detectaron canciones nuevas. No hay nada que publicar.")
        return

    print(f"Se detectaron {len(nuevas_canciones)} canción(es) nueva(s).\n")

    publicadas = 0
    errores = 0

    for numero, cancion in enumerate(
        nuevas_canciones,
        start=1
    ):

        print(f"[PUBLICACIÓN {numero}/{len(nuevas_canciones)}]")
        print(f"Artista(s): {cancion['artistas']}")
        print(f"Canción: {cancion['titulo']}")

        exito, error = (
            publicar_cancion(
                cancion
            )
        )

        if exito:
            print("PUBLICADA CORRECTAMENTE")

            canciones_publicadas.add(
                cancion["id"]
            )

            guardar_estado(
                estado
            )

            publicadas += 1

        else:
            print("ERROR AL PUBLICAR")
            print(error)

            errores += 1

            enviar_alerta_error(
                cancion,
                "Publicación en Telegram",
                error,
            )

        print()

    print("=" * 60)
    print("RESUMEN DE LA EJECUCIÓN")
    print(f"Nuevas detectadas: {len(nuevas_canciones)}")
    print(f"Publicadas: {publicadas}")
    print(f"Errores: {errores}")
    print("=" * 60)


if __name__ == "__main__":
    main()
