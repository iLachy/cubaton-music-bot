import os
import json
import html
import unicodedata
import re
from datetime import datetime, timezone
from io import BytesIO

import requests
from PIL import Image, ImageOps
from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

TELEGRAM_CHAT_ID = "@Cubaton_Music"
TELEGRAM_ALERT_CHAT_ID = "@CubatonMusicBot"

STATE_FILE = "state/releases.json"

# ============================================================
# MODO PRUEBA
# ============================================================
# IMPORTANTE:
# En este modo state/releases.json puede LEERSE para detectar canciones
# ya registradas, pero NUNCA se modifica durante la ejecución.
# Una canción publicada correctamente NO se agrega al estado.
# Esto permite repetir pruebas sobre la misma canción.
MODO_PRUEBA = True

# Tamaño final de las portadas enviadas a Telegram.
TAMANO_PORTADA = 544

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


# ============================================================
# ARTISTAS MONITORIZADOS
# ============================================================

ARTISTAS = [
    {"nombre": "Bebeshito", "channel_id": "UCpVfWS-cPOE2sYqsFuuP_Qg"},
    {"nombre": "Charly & Johayron", "channel_id": "UCnwEtOQyXJUUuBhcTgImdfQ"},
    {"nombre": "Dany Ome", "channel_id": "UCJQEm9t4KjDn-I8Fahf4Uqw"},
    {"nombre": "Wampi", "channel_id": "UCbfzw8u1lCwDMv443StJEOw"},
    {"nombre": "El Taiger", "channel_id": "UCoYtt7bGCV5RyUweyQgqQ4A"},
    {"nombre": "Ja Rulay", "channel_id": "UCcaU4COep7mj8kbXwS24JFQ"},
    {"nombre": "L Kimii", "channel_id": "UCMyQosiL8iVUtXPIm1UZJQg"},
    {"nombre": "El Dray", "channel_id": "UC4kpn8y8QXYXmyDn8HJKD8Q"},
    {"nombre": "Mauro y El Pitu", "channel_id": "UCvN1mRFfAfWYTiIkM70qUWA"},
    {"nombre": "Yirow Y El Tingo", "channel_id": "UCEq3_5h1Xi_vLbytP7OzuNA"},
    {"nombre": "Nany La Kbra", "channel_id": "UCG4lSNdNx_LuLnN2EW6uWwQ"},
    {"nombre": "Ya Ice Dilan", "channel_id": "UC9aJbR9Q8nscvZaMw_cH4Ww"},
    {"nombre": "Rey Tony", "channel_id": "UCDhExL0uVtumv_DEjPPq5qg"},
    {"nombre": "Baby Maikol", "channel_id": "UCP5R6Mgbk_bgtgzZguLNKdA"},
    {"nombre": "Payaso X Ley", "channel_id": "UCauTaqBvFqqqJTu3B4Wc1GA"},
    {"nombre": "Kaly Y Kowa", "channel_id": "UCSfR51myQhs2ZcdzrWo0Z4w"},
    {"nombre": "Wildey", "channel_id": "UCmFS-VSa4Wf3F1wdWS-8p_g"},
    {"nombre": "Wow Popy", "channel_id": "UCtFkN8UFxT_MuNdySlfuFuA"},
    {"nombre": "Talent Fuego", "channel_id": "UC0dVmcXfNa7lVeUBve3_FXw"},
    {"nombre": "Mawell", "channel_id": "UCL6P-jUDZEKBA-Lb6WFccWg"},
    {"nombre": "Harryson", "channel_id": "UC2ihX5uoblnN4wsA-ayIAAA"},
    {"nombre": "El Chulo", "channel_id": "UCiT8VNdnpeYnCTPJZoqym9g"},
    {"nombre": "Fixty Ordara", "channel_id": "UCDHDCbVOQywsLCsCZ8PH-AA"},
    {"nombre": "El Kamel", "channel_id": "UCPnWcazEV7QM0H7qBx6NVXg"},
    {"nombre": "Velito el Bufón", "channel_id": "UCRA9cRfAJXuxDRcFnoB7pwg"},
    {"nombre": "Un Titico", "channel_id": "UCT2KiGFSPZIF3DR9UIN2fYw"},
    {
        "nombre": "Musteerifa",
        "channel_id": "UCiT8PzlQqtPC7lWFh3--4jw",
        "channel_ids": [
            "UCiT8PzlQqtPC7lWFh3--4jw",
            "UCUmbJ10w6Sljv-zIv0iQxNw",
        ],
        "channels_solo_ultima_nueva": [
            "UCUmbJ10w6Sljv-zIv0iQxNw",
        ],
    },
    {
        "nombre": "Los Dele",
        "channel_id": "UCe9SuCBefzhTyPCgiMMvcbA",
        "solo_ultima_nueva": True,
    },
    {"nombre": "Chocolate MC", "channel_id": "UCYVuThmAmbXxk1o9Un5Cc_w"},
    {"nombre": "El Chacal", "channel_id": "UCJt4IsSmUjqTaamhCJoKK_g"},
    {"nombre": "El Micha", "channel_id": "UCHhrMSqe_C1E_JBEz3mRlew"},
    {"nombre": "Yomil", "channel_id": "UCPfXwOpwRIbVsqqTsgt4i5g"},
    {"nombre": "Jacob Forever", "channel_id": "UCJ1-Pwsroy-gzMqlfKDF4Hg"},
    {"nombre": "Gente de Zona", "channel_id": "UCl2KQVc_GFH081i7b9CJQug"},
    {"nombre": "La Diosa", "channel_id": "UChbVOQHgq01JoHY4axuWV0A"},
    {"nombre": "Seidy La Niña", "channel_id": "UCFqYfgj_7h3ZUkBnyYS-TFg"},
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


def normalizar_titulo_album(titulo):
    """Normaliza un título para detectar álbumes equivalentes."""
    texto = " ".join(str(titulo or "").strip().split()).casefold()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(
        caracter for caracter in texto if not unicodedata.combining(caracter)
    )


# ============================================================
# ESTADO
# ============================================================

ESTADO_VERSION = 2


def cargar_estado():
    """Carga el estado existente. En modo prueba solo se lee."""
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as archivo:
            estado = json.load(archivo)

        if not isinstance(estado, dict):
            return None

        if estado.get("version") != ESTADO_VERSION:
            print("Estado antiguo detectado.")
            print("Se requiere un state/releases.json de versión compatible.")
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
    """Guarda el estado, excepto cuando MODO_PRUEBA está activo."""
    if MODO_PRUEBA:
        print("MODO PRUEBA: state/releases.json NO se modificará.")
        return

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

    claves = {normalizar_nombre(nombre) for nombre in nombres}
    tiene_rey_tony = "rey tony" in claves
    tiene_helabusador = "helabusador" in claves

    if tiene_rey_tony and tiene_helabusador:
        resultado = []
        for nombre in nombres:
            clave = normalizar_nombre(nombre)
            if clave in ("rey tony", "helabusador"):
                continue
            resultado.append(nombre)
        resultado.insert(0, "Rey Tony & Helabusador")
        nombres = resultado

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
    nombre_publicacion = "Single" if tipo_lanzamiento == "Single" else (titulo_lanzamiento or "Sin título")
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

def obtener_anio_para_track(ytmusic, track, titulo, artistas):
    """Obtiene el año de un track del fallback aunque no venga en el track."""
    anio_directo = track.get("year")
    if anio_directo:
        return str(anio_directo)

    nombres = [str(a).strip() for a in artistas if a]
    claves_artistas = {normalizar_nombre(x) for x in nombres}

    album = track.get("album")
    album_ids = []
    titulo_album = None

    if isinstance(album, dict):
        titulo_album = album.get("name") or album.get("title")
        album_id = album.get("id") or album.get("browseId")
        if album_id:
            album_ids.append(album_id)

    for album_id in album_ids:
        try:
            datos_album = ytmusic.get_album(album_id)
            if datos_album and datos_album.get("year"):
                return str(datos_album.get("year"))
        except Exception:
            pass

    consultas = []
    if nombres:
        consultas.append(f"{titulo} {nombres[0]}")
    consultas.append(str(titulo))

    vistos = set()
    for consulta in consultas:
        clave = consulta.casefold()
        if clave in vistos:
            continue
        vistos.add(clave)

        try:
            resultados = ytmusic.search(consulta, filter="songs", limit=20, ignore_spelling=True)
        except Exception:
            continue

        for resultado in resultados:
            titulo_resultado = str(resultado.get("title", "")).strip()
            if titulo_resultado.casefold() != str(titulo).casefold():
                continue

            video_resultado = resultado.get("videoId")
            video_original = track.get("videoId")
            if video_original and video_resultado and video_resultado != video_original:
                continue

            artistas_resultado = extraer_artistas_de_objetos(resultado.get("artists"))
            if claves_artistas and artistas_resultado:
                claves_resultado = {normalizar_nombre(x) for x in artistas_resultado}
                if not (claves_artistas & claves_resultado):
                    continue

            album_resultado = resultado.get("album")
            album_resultado_id = None
            if isinstance(album_resultado, dict):
                album_resultado_id = album_resultado.get("id") or album_resultado.get("browseId")
                if not titulo_album:
                    titulo_album = album_resultado.get("name") or album_resultado.get("title")

            if album_resultado_id and album_resultado_id not in album_ids:
                album_ids.append(album_resultado_id)

            for album_id in album_ids:
                try:
                    datos_album = ytmusic.get_album(album_id)
                    if datos_album and datos_album.get("year"):
                        return str(datos_album.get("year"))
                except Exception:
                    pass

    consultas_album = []
    if titulo_album:
        consultas_album.append(titulo_album)
    consultas_album.append(str(titulo))

    vistos_album = set()
    for consulta in consultas_album:
        clave = consulta.casefold()
        if clave in vistos_album:
            continue
        vistos_album.add(clave)

        try:
            resultados = ytmusic.search(consulta, filter="albums", limit=20, ignore_spelling=True)
        except Exception:
            continue

        for resultado in resultados:
            titulo_resultado = str(resultado.get("title", "")).strip()
            if titulo_album and titulo_resultado.casefold() != str(titulo_album).casefold():
                continue

            album_id = resultado.get("browseId") or resultado.get("albumId")
            if not album_id:
                continue

            try:
                datos_album = ytmusic.get_album(album_id)
                if datos_album and datos_album.get("year"):
                    return str(datos_album.get("year"))
            except Exception:
                pass

    return ""


def obtener_lanzamientos_fuente_nueva(ytmusic, channel_id, nombre, canciones_procesadas):
    """Obtiene de forma completa los lanzamientos de una fuente nueva."""
    canciones = []

    try:
        datos = ytmusic.get_artist(channel_id)
    except Exception as error:
        print(f"ERROR obteniendo artista {nombre} (canal {channel_id}): {error}")
        return canciones

    def procesar_lista_completa(clave):
        bloque = datos.get(clave, {})
        browse_id = bloque.get("browseId")
        params = bloque.get("params")
        if not browse_id or not params:
            return

        try:
            lanzamientos = ytmusic.get_artist_albums(
                browse_id, params, limit=None, order="Recency"
            )
        except Exception as error:
            print(f"ERROR obteniendo lista completa de {clave} para {nombre} ({channel_id}): {error}")
            return

        for lanzamiento in lanzamientos:
            release_browse_id = lanzamiento.get("browseId")
            if not release_browse_id:
                continue

            titulo_lanzamiento = lanzamiento.get("title", "Sin título")
            tipo_lanzamiento = lanzamiento.get("type", "Album")
            tipo_normalizado = str(tipo_lanzamiento).strip()

            if tipo_normalizado.casefold() == "ep":
                tipo_normalizado = "EP"
            elif tipo_normalizado.casefold() in ("album", "álbum"):
                tipo_normalizado = "Album"
            elif clave == "singles":
                tipo_normalizado = "Single"

            anio = lanzamiento.get("year", "")

            try:
                datos_lanzamiento = ytmusic.get_album(release_browse_id)
            except Exception as error:
                print(f"No se pudo obtener el lanzamiento {titulo_lanzamiento} ({release_browse_id}): {error}")
                continue

            if not datos_lanzamiento:
                continue

            tipo_datos = datos_lanzamiento.get("type")
            if tipo_datos:
                tipo_normalizado = str(tipo_datos).strip()
                if tipo_normalizado.casefold() == "ep":
                    tipo_normalizado = "EP"
                elif tipo_normalizado.casefold() in ("album", "álbum"):
                    tipo_normalizado = "Album"

            anio_datos = datos_lanzamiento.get("year")
            if anio_datos:
                anio = anio_datos

            tracks = datos_lanzamiento.get("tracks", [])
            if not tracks:
                continue

            print(f"Fuente nueva -> {tipo_normalizado}: {titulo_lanzamiento} -> {len(tracks)} canciones")

            for track in tracks:
                video_id = track.get("videoId")
                if not video_id:
                    continue

                cancion_id = f"video:{video_id}"
                if cancion_id in canciones_procesadas:
                    continue

                cancion = crear_cancion_desde_track(
                    track,
                    nombre,
                    tipo_normalizado,
                    anio,
                    titulo_lanzamiento=titulo_lanzamiento,
                    album_browse_id=release_browse_id,
                )
                if not cancion:
                    continue

                cancion["_canal_origen"] = channel_id
                cancion["_orden_origen"] = len(canciones)
                cancion["_fuente_solo_ultima"] = True
                canciones.append(cancion)
                canciones_procesadas.add(cancion_id)

    procesar_lista_completa("singles")
    procesar_lista_completa("albums")

    if not canciones:
        bloque_canciones = datos.get("songs", {})
        songs_browse_id = bloque_canciones.get("browseId")

        if songs_browse_id:
            try:
                playlist = ytmusic.get_playlist(songs_browse_id, limit=None)
                tracks = playlist.get("tracks", [])

                if tracks:
                    print(f"Fuente nueva -> Songs fallback: {len(tracks)} canciones")

                for indice, track in enumerate(tracks):
                    video_id = track.get("videoId")
                    titulo = track.get("title")
                    if not video_id or not titulo:
                        continue

                    cancion_id = f"video:{video_id}"
                    if cancion_id in canciones_procesadas:
                        continue

                    artistas = extraer_artistas_de_objetos(track.get("artists"))
                    if not artistas:
                        artista_track = track.get("artist")
                        if artista_track:
                            artistas = [artista_track]
                    if not artistas:
                        artistas = [nombre]

                    track_para_cancion = dict(track)
                    track_para_cancion["videoId"] = video_id
                    track_para_cancion["title"] = titulo
                    track_para_cancion["artists"] = [{"name": artista_nombre} for artista_nombre in artistas]

                    cancion = crear_cancion_desde_track(
                        track_para_cancion,
                        nombre,
                        "Single",
                        obtener_anio_para_track(ytmusic, track, titulo, artistas),
                        titulo_lanzamiento=titulo,
                    )
                    if not cancion:
                        continue

                    cancion["_canal_origen"] = channel_id
                    cancion["_orden_origen"] = indice
                    cancion["_fuente_solo_ultima"] = True
                    canciones.append(cancion)
                    canciones_procesadas.add(cancion_id)

            except Exception as error:
                print(f"ERROR en Songs fallback para {nombre} ({channel_id}): {error}")

    return canciones


def obtener_lanzamientos_artista(ytmusic, artista):
    """Obtiene canciones individuales de uno o varios canales."""
    nombre = artista["nombre"]
    channel_ids = artista.get("channel_ids")

    if not channel_ids:
        channel_id = artista.get("channel_id")
        if not channel_id:
            print(f"ERROR: {nombre} no tiene ningún channel_id configurado.")
            return []
        channel_ids = [channel_id]

    print(f"Comprobando: {nombre}")
    canciones = []
    canciones_procesadas = set()
    albumes_procesados = set()

    canales_solo_ultima = set(artista.get("channels_solo_ultima_nueva", []))
    artista_es_nuevo = bool(artista.get("solo_ultima_nueva", False))

    for numero_canal, channel_id in enumerate(channel_ids, start=1):
        if len(channel_ids) > 1:
            print(f"  Canal {numero_canal}/{len(channel_ids)}: {channel_id}")

        fuente_nueva = artista_es_nuevo or channel_id in canales_solo_ultima
        if fuente_nueva:
            canciones_nuevas = obtener_lanzamientos_fuente_nueva(
                ytmusic, channel_id, nombre, canciones_procesadas
            )
            canciones.extend(canciones_nuevas)
            continue

        try:
            datos = ytmusic.get_artist(channel_id)
        except Exception as error:
            print(f"ERROR obteniendo artista {nombre} (canal {channel_id}): {error}")
            continue

        singles = datos.get("singles", {})
        resultados_singles = singles.get("results", [])

        for single in resultados_singles:
            video_id = single.get("videoId")
            if not video_id:
                continue
            cancion_id = f"video:{video_id}"
            if cancion_id in canciones_procesadas:
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
                    "artists": [{"name": artista_nombre} for artista_nombre in artistas],
                },
                nombre,
                "Single",
                anio,
                titulo_lanzamiento=titulo,
            )

            if cancion:
                cancion["_canal_origen"] = channel_id
                cancion["_orden_origen"] = len(canciones)
                cancion["_fuente_solo_ultima"] = artista_es_nuevo or channel_id in canales_solo_ultima
                canciones.append(cancion)
                canciones_procesadas.add(cancion_id)

        albums = datos.get("albums", {})
        resultados_albums = albums.get("results", [])

        for album in resultados_albums:
            browse_id = album.get("browseId")
            if not browse_id:
                continue

            titulo_album = album.get("title", "Sin título")
            tipo_album = album.get("type", "Album")
            clave_album = (
                normalizar_titulo_album(titulo_album),
                normalizar_nombre(tipo_album),
                str(album.get("year", "") or "").strip(),
            )

            if clave_album in albumes_procesados:
                print(f"Álbum equivalente omitido: {titulo_album}")
                continue
            albumes_procesados.add(clave_album)

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
            if not tracks:
                print(f"Sin pistas disponibles: {titulo_album}")
                continue

            print(f"{tipo_normalizado}: {titulo_album} -> {len(tracks)} canciones")

            for track in tracks:
                video_id = track.get("videoId")
                if not video_id:
                    continue

                cancion_id = f"video:{video_id}"
                if cancion_id in canciones_procesadas:
                    continue

                cancion = crear_cancion_desde_track(
                    track,
                    nombre,
                    tipo_normalizado,
                    anio,
                    titulo_lanzamiento=titulo_album,
                    album_browse_id=browse_id,
                )

                if cancion:
                    cancion["_canal_origen"] = channel_id
                    cancion["_orden_origen"] = len(canciones)
                    cancion["_fuente_solo_ultima"] = artista_es_nuevo or channel_id in canales_solo_ultima
                    canciones.append(cancion)
                    canciones_procesadas.add(cancion_id)

    return canciones


def _anio_numerico(cancion):
    try:
        return int(str(cancion.get("anio") or "0").strip())
    except (TypeError, ValueError):
        return 0


def seleccionar_ultima_cancion(canciones):
    if not canciones:
        return None

    mejores = sorted(
        canciones,
        key=lambda cancion: (
            _anio_numerico(cancion),
            1 if cancion.get("tipo") == "Single" else 0,
            -int(cancion.get("_orden_origen", 0)),
        ),
        reverse=True,
    )
    return mejores[0]


def preparar_nuevas_fuentes(canciones, canciones_publicadas):
    """Mantiene la regla de solo la última para fuentes nuevas."""
    grupos = {}

    for cancion in canciones:
        if not cancion.get("_fuente_solo_ultima"):
            continue
        canal = cancion.get("_canal_origen")
        if not canal:
            continue
        grupos.setdefault(canal, []).append(cancion)

    ultimas = {}
    for canal, grupo in grupos.items():
        ultima = seleccionar_ultima_cancion(grupo)
        if not ultima:
            continue

        ultima_id = ultima["id"]
        ultimas[canal] = ultima_id

        for cancion in grupo:
            if cancion["id"] == ultima_id:
                continue
            # Esto solo modifica la copia en memoria del set.
            # En MODO_PRUEBA jamás se guarda al disco.
            canciones_publicadas.add(cancion["id"])

    resultado = []
    for cancion in canciones:
        if not cancion.get("_fuente_solo_ultima"):
            resultado.append(cancion)
            continue

        canal = cancion.get("_canal_origen")
        ultima_id = ultimas.get(canal)
        if cancion["id"] == ultima_id:
            resultado.append(cancion)

    return resultado


# ============================================================
# PORTADA DE YOUTUBE MUSIC
# ============================================================

def _extraer_urls_portada(resultado):
    """Devuelve las miniaturas de YouTube Music ordenadas por resolución."""
    urls = []

    thumbnails = resultado.get("thumbnails") or []
    if isinstance(thumbnails, list):
        candidatas = []
        for thumb in thumbnails:
            if not isinstance(thumb, dict):
                continue

            url = thumb.get("url")
            if not url:
                continue

            try:
                width = int(thumb.get("width") or 0)
            except (TypeError, ValueError):
                width = 0

            try:
                height = int(thumb.get("height") or 0)
            except (TypeError, ValueError):
                height = 0

            candidatas.append((max(width, height), width, height, url))

        candidatas.sort(reverse=True)
        for _, _, _, url in candidatas:
            if url not in urls:
                urls.append(url)

    return urls


def buscar_portada_youtube_music(ytmusic, cancion):
    """
    Busca la portada real de YouTube Music.

    Prioridad:
    1. Datos completos del video con get_song(), usando la miniatura de mayor
       resolución que YouTube Music entregue realmente.
    2. Resultado de búsqueda exacto de la canción.
    3. Álbum asociado al resultado.

    No se fabrican URLs w544-h544 a partir de una URL w120-h120.
    """
    titulo = str(cancion.get("titulo") or "").strip()
    artistas = str(cancion.get("artistas") or "").strip()
    video_id = cancion.get("video_id")
    consulta = " ".join(x for x in (titulo, artistas) if x)

    print()
    print(f"Buscando portada en YouTube Music: {consulta}")

    # --------------------------------------------------------
    # 1. Obtener información completa del video concreto.
    # --------------------------------------------------------
    if video_id:
        try:
            datos_song = ytmusic.get_song(video_id)
            urls = _extraer_urls_portada(datos_song)
            if urls:
                return urls[0]

            album_song = datos_song.get("album")
            if isinstance(album_song, dict):
                urls = _extraer_urls_portada(album_song)
                if urls:
                    return urls[0]
        except Exception as error:
            print(f"No se pudo obtener get_song() para {video_id}: {error}")

    # --------------------------------------------------------
    # 2. Buscar la canción en YouTube Music.
    # --------------------------------------------------------
    consultas = [consulta]
    if titulo:
        consultas.append(titulo)

    vistos_consulta = set()

    for consulta_actual in consultas:
        clave_consulta = consulta_actual.casefold()
        if not consulta_actual or clave_consulta in vistos_consulta:
            continue
        vistos_consulta.add(clave_consulta)

        try:
            resultados = ytmusic.search(
                consulta_actual,
                filter="songs",
                limit=10,
                ignore_spelling=True,
            )
        except Exception as error:
            print(f"Error buscando canciones en YouTube Music: {error}")
            resultados = []

        for resultado in resultados:
            if not isinstance(resultado, dict):
                continue

            titulo_resultado = str(resultado.get("title") or "").strip()
            if titulo and titulo_resultado.casefold() != titulo.casefold():
                continue

            video_resultado = resultado.get("videoId")
            if video_id and video_resultado and video_resultado != video_id:
                continue

            urls = _extraer_urls_portada(resultado)
            if urls:
                return urls[0]

            album = resultado.get("album")
            if isinstance(album, dict):
                urls = _extraer_urls_portada(album)
                if urls:
                    return urls[0]

    # --------------------------------------------------------
    # 3. Último intento: buscar el álbum.
    # --------------------------------------------------------
    for consulta_actual in consultas:
        if not consulta_actual:
            continue

        try:
            resultados = ytmusic.search(
                consulta_actual,
                filter="albums",
                limit=10,
                ignore_spelling=True,
            )
        except Exception:
            resultados = []

        for resultado in resultados:
            if not isinstance(resultado, dict):
                continue

            urls = _extraer_urls_portada(resultado)
            if urls:
                return urls[0]

    return None


def descargar_portada_youtube_music(ytmusic, cancion):
    """Descarga la portada de YouTube Music y la prepara a 544x544."""
    url = buscar_portada_youtube_music(ytmusic, cancion)

    if not url:
        raise RuntimeError("No se encontró una portada de YouTube Music compatible.")

    print(f"Portada de YouTube Music encontrada: {url}")

    respuesta = requests.get(url, timeout=30)
    respuesta.raise_for_status()

    imagen = Image.open(BytesIO(respuesta.content)).convert("RGB")
    print(f"Dimensiones originales de portada: {imagen.size[0]}x{imagen.size[1]}")

    imagen_cuadrada = ImageOps.fit(
        imagen,
        (TAMANO_PORTADA, TAMANO_PORTADA),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )

    if imagen_cuadrada.size != (TAMANO_PORTADA, TAMANO_PORTADA):
        raise RuntimeError(
            f"La portada no quedó cuadrada: {imagen_cuadrada.size}"
        )

    print(
        f"Dimensiones finales de portada: "
        f"{imagen_cuadrada.size[0]}x{imagen_cuadrada.size[1]}"
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
            f"❌ <b>Error:</b>\n{escapar(detalle)}\n\n"
            "🔄 La canción NO se marcará como publicada y será intentada nuevamente en la próxima ejecución."
        )

        respuesta = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": TELEGRAM_ALERT_CHAT_ID,
                "text": mensaje,
                "parse_mode": "HTML",
            },
            timeout=30,
        )

        if not respuesta.ok:
            print(f"No se pudo enviar la alerta de Telegram: {respuesta.text}")

    except Exception as error:
        print(f"No se pudo enviar la alerta de error: {error}")


# ============================================================
# PUBLICAR CANCIÓN
# ============================================================

def publicar_cancion(ytmusic, cancion):
    """Publica una canción usando la portada real de YouTube Music."""
    titulo = escapar(cancion["titulo"])
    artistas = escapar(cancion["artistas"])
    nombre_publicacion = escapar(cancion["nombre_publicacion"])
    anio = escapar(cancion["anio"])

    caption = (
        f"🎤 <b>{artistas}</b>\n"
        f"<blockquote>🎵 <b>{titulo}</b></blockquote>\n"
        f"📀 <i>{nombre_publicacion}</i>\n"
        f"🗓 {anio}\n"
        f"\n"
        f"@Cubaton_Music"
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

    try:
        buffer = descargar_portada_youtube_music(ytmusic, cancion)
    except Exception as error:
        return False, f"No se pudo preparar la portada de YouTube Music: {error}"

    try:
        respuesta = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(reply_markup, ensure_ascii=False),
            },
            files={
                "photo": (
                    f"{cancion['video_id']}.jpg",
                    buffer,
                    "image/jpeg",
                )
            },
            timeout=60,
        )

        if not respuesta.ok:
            return False, respuesta.text

        datos = respuesta.json()
        if not datos.get("ok"):
            return False, str(datos)

        print("PUBLICACIÓN ENVIADA CORRECTAMENTE")
        return True, None

    except Exception as error:
        return False, str(error)


# ============================================================
# LÍNEA BASE
# ============================================================

def crear_linea_base(ytmusic):
    """
    En MODO_PRUEBA no se crea línea base porque eso modificaría
    state/releases.json. Se informa y se detiene la ejecución.
    """
    print()
    print("NO SE PUEDE CREAR LA LÍNEA BASE EN MODO PRUEBA")
    print("state/releases.json debe existir antes de realizar las pruebas.")
    print("Para evitar modificaciones accidentales, la ejecución se detendrá.")
    print()
    return None


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("=" * 60)
    print("CUBATON MUSIC BOT - PRUEBA DIRECTA")
    print("=" * 60)
    print()

    print("⚠️ MODO PRUEBA DIRECTA: PAL PISO")
    print("state/releases.json NO será leído ni modificado.")
    print(f"Portada final: {TAMANO_PORTADA}x{TAMANO_PORTADA}")
    print()

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No existe el secreto TELEGRAM_BOT_TOKEN.")
        return

    ytmusic = YTMusic()

    cancion_prueba = {
        "id": "video:AU_l1Rn_nJI",
        "video_id": "AU_l1Rn_nJI",
        "titulo": "Pal Piso",
        "artistas": "LA R, Musteerifa, Vittorio Di Benedetto",
        "tipo": "Single",
        "anio": "2026",
        "nombre_publicacion": "Single",
        "youtube_url": "https://music.youtube.com/watch?v=AU_l1Rn_nJI",
        "artista_monitorizado": "Musteerifa",
        "titulo_lanzamiento": "Pal Piso",
        "album_browse_id": None,
    }

    print("Video ID: AU_l1Rn_nJI")
    print("Título: Pal Piso")
    print("Artistas: LA R, Musteerifa, Vittorio Di Benedetto")
    print("Tipo: Single")
    print("Año: 2026")
    print("Estado: NO SE LEERÁ NI MODIFICARÁ")
    print()
    print("=" * 60)
    print()

    print("[PRUEBA 1/1]")
    print(f"Artista(s): {cancion_prueba['artistas']}")
    print(f"Canción: {cancion_prueba['titulo']}")
    print(f"Lanzamiento: {cancion_prueba['nombre_publicacion']}")
    print(f"Año: {cancion_prueba['anio']}")
    print()

    exito, error = publicar_cancion(ytmusic, cancion_prueba)

    print()
    print("=" * 60)
    print("RESUMEN DE LA PRUEBA")

    if exito:
        print("PUBLICACIÓN ENVIADA CORRECTAMENTE")
        print("state/releases.json NO FUE LEÍDO NI MODIFICADO.")
        print("La canción puede volver a probarse en la siguiente ejecución.")
    else:
        print("ERROR AL PUBLICAR")
        print(error)
        print("state/releases.json NO FUE LEÍDO NI MODIFICADO.")
        enviar_alerta_error(
            cancion_prueba,
            "Prueba directa de publicación",
            error,
        )

    print("=" * 60)


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":
    main()
