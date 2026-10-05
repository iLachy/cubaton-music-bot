import os
import re
import json
import html
import unicodedata
from datetime import datetime, timezone
from io import BytesIO

import requests
from PIL import Image
from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

TELEGRAM_CHAT_ID = "@Cubaton_Music"
TELEGRAM_ALERT_CHAT_ID = os.environ.get("TELEGRAM_ALERT_CHAT_ID")

# ============================================================
# SEGURIDAD DEL FALLBACK
# ============================================================
# La búsqueda por artista es complementaria y puede devolver canciones
# del catálogo que no pertenecen a los listados habituales del canal.
# Por seguridad queda DESACTIVADA por defecto hasta validarla de forma
# controlada. Los canales configurados siguen funcionando normalmente.
ACTIVAR_BUSQUEDA_ADICIONAL_POR_ARTISTA = False

# No se publican canciones cuyo año sea anterior al año actual menos este
# valor (1 = solo año actual y anterior). Las descartadas se registran como
# históricas. Para pruebas con canciones antiguas, súbelo temporalmente.
MAX_ANTIGUEDAD_ANIOS = 1

# Si no se logra resolver el álbum para obtener la portada, publicar la
# canción solo con texto y botón (True) en lugar de reintentar y enviar
# una alerta en cada ejecución (False).
PUBLICAR_SIN_PORTADA_SI_FALLA = True

# Envía debajo de cada publicación un adelanto de unos 30 segundos
# (preview oficial que ofrece Deezer para promoción). Si no se encuentra
# la canción o falla el envío, simplemente no se envía y no se genera alerta.
ENVIAR_PREVIEW_AUDIO = True

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
        "channel_ids": [
            "UCiT8PzlQqtPC7lWFh3--4jw",
            "UCUmbJ10w6Sljv-zIv0iQxNw",
        ],
        # El segundo canal se incorpora como nueva fuente.
        # En su primera integración se publica solamente
        # su lanzamiento más reciente y el resto queda
        # registrado como histórico.
        "channels_solo_ultima_nueva": [
            "UCUmbJ10w6Sljv-zIv0iQxNw",
        ],
    },
    {
        "nombre": "Los Dele",
        "channel_id": "UCe9SuCBefzhTyPCgiMMvcbA",
        # Artista nuevo: en la primera integración se publica
        # solamente su lanzamiento más reciente.
        "solo_ultima_nueva": True,
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


def normalizar_titulo_album(titulo):
    """Normaliza un título para detectar álbumes equivalentes."""
    texto = " ".join(
        str(titulo or "").strip().split()
    ).casefold()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    return "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )


# ============================================================
# ESTADO
# ============================================================

def clave_cancion(cancion):
    """
    Clave estable (artista + título) para detectar la misma canción
    aunque YouTube Music le asigne IDs distintos (single, álbum, video).
    """
    artistas = normalizar_titulo_album(cancion.get("artistas"))
    titulo = normalizar_titulo_album(cancion.get("titulo"))
    return f"k:{artistas}|{titulo}"


ESTADO_VERSION = 2


def cargar_estado():
    """
    Carga el estado.

    La versión 2 guarda cada canción individualmente.
    """

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
    """
    Formatea los artistas acreditados.

    Ejemplos:

    Bebeshito

    Bebeshito, Dj Honda

    Bebeshito, Charly & Johayron, Dany Ome

    Excepción:

    Rey Tony + Helabusador
    -> Rey Tony & Helabusador
    """

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
    """
    Obtiene información completa
    de un EP o álbum.
    """

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
):
    """
    Convierte una pista de YouTube Music
    en una canción individual.

    La publicación mostrará:

    📀 Single

    o:

    📀 Nombre del EP

    o:

    📀 Nombre del Álbum
    """

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

    return {

        # Identificador único de la canción
        "id": f"video:{video_id}",

        "video_id": video_id,

        "titulo": titulo,

        "artistas": (
            artistas_formateados
        ),

        # Single / EP / Album
        "tipo": tipo_lanzamiento,

        "anio": str(
            anio or ""
        ),

        # Esto es lo que aparecerá
        # después del icono 📀
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

    # 1. Intentar directamente con el álbum asociado al track.
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

    # 2. Buscar la canción exacta y utilizar el álbum que YouTube Music
    #    asocia al resultado. También comprobamos el videoId cuando existe.
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
            resultados = ytmusic.search(
                consulta,
                filter="songs",
                limit=20,
                ignore_spelling=True,
            )
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

            artistas_resultado = extraer_artistas_de_objetos(
                resultado.get("artists")
            )

            if claves_artistas and artistas_resultado:
                claves_resultado = {normalizar_nombre(x) for x in artistas_resultado}
                if not (claves_artistas & claves_resultado):
                    continue

            album_resultado = resultado.get("album")
            album_resultado_id = None
            if isinstance(album_resultado, dict):
                album_resultado_id = (
                    album_resultado.get("id")
                    or album_resultado.get("browseId")
                )
                if not titulo_album:
                    titulo_album = (
                        album_resultado.get("name")
                        or album_resultado.get("title")
                    )

            if album_resultado_id and album_resultado_id not in album_ids:
                album_ids.append(album_resultado_id)

            for album_id in album_ids:
                try:
                    datos_album = ytmusic.get_album(album_id)
                    if datos_album and datos_album.get("year"):
                        return str(datos_album.get("year"))
                except Exception:
                    pass

    # 3. Último intento: buscar el álbum/single por su título.
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
            resultados = ytmusic.search(
                consulta,
                filter="albums",
                limit=20,
                ignore_spelling=True,
            )
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


def obtener_lanzamientos_fuente_nueva(
    ytmusic,
    channel_id,
    nombre,
    canciones_procesadas,
):
    """
    Obtiene de forma completa los lanzamientos de una fuente nueva.

    YouTube Music puede mostrar en get_artist() solamente una lista
    resumida. Para una fuente nueva necesitamos consultar las listas
    completas de singles y álbumes/EP mediante get_artist_albums().
    """

    canciones = []

    try:
        datos = ytmusic.get_artist(channel_id)
    except Exception as error:
        print(
            f"ERROR obteniendo artista {nombre} "
            f"(canal {channel_id}): {error}"
        )
        return canciones

    # ------------------------------------------------------------
    # Procesar una lista completa de lanzamientos.
    # ------------------------------------------------------------
    def procesar_lista_completa(clave):
        bloque = datos.get(clave, {})

        browse_id = bloque.get("browseId")
        params = bloque.get("params")

        if not browse_id or not params:
            return

        try:
            lanzamientos = ytmusic.get_artist_albums(
                browse_id,
                params,
                limit=None,
                order="Recency",
            )
        except Exception as error:
            print(
                f"ERROR obteniendo lista completa de {clave} "
                f"para {nombre} ({channel_id}): {error}"
            )
            return

        for lanzamiento in lanzamientos:
            release_browse_id = lanzamiento.get("browseId")

            if not release_browse_id:
                continue

            titulo_lanzamiento = lanzamiento.get(
                "title",
                "Sin título"
            )

            tipo_lanzamiento = lanzamiento.get(
                "type",
                "Album"
            )

            tipo_normalizado = str(
                tipo_lanzamiento
            ).strip()

            if tipo_normalizado.casefold() == "ep":
                tipo_normalizado = "EP"
            elif tipo_normalizado.casefold() in (
                "album",
                "álbum",
            ):
                tipo_normalizado = "Album"
            else:
                # La sección de singles corresponde a Single.
                if clave == "singles":
                    tipo_normalizado = "Single"

            anio = lanzamiento.get("year", "")

            try:
                datos_lanzamiento = ytmusic.get_album(
                    release_browse_id
                )
            except Exception as error:
                print(
                    f"No se pudo obtener el lanzamiento "
                    f"{titulo_lanzamiento} ({release_browse_id}): "
                    f"{error}"
                )
                continue

            if not datos_lanzamiento:
                continue

            tipo_datos = datos_lanzamiento.get("type")
            if tipo_datos:
                tipo_normalizado = str(
                    tipo_datos
                ).strip()

                if tipo_normalizado.casefold() == "ep":
                    tipo_normalizado = "EP"
                elif tipo_normalizado.casefold() in (
                    "album",
                    "álbum",
                ):
                    tipo_normalizado = "Album"

            anio_datos = datos_lanzamiento.get("year")
            if anio_datos:
                anio = anio_datos

            tracks = datos_lanzamiento.get("tracks", [])
            if not tracks:
                continue

            print(
                f"Fuente nueva -> {tipo_normalizado}: "
                f"{titulo_lanzamiento} -> "
                f"{len(tracks)} canciones"
            )

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

    # ------------------------------------------------------------
    # Fallback para canales que no exponen correctamente las
    # pestañas de singles/álbumes. En esos casos get_artist()
    # puede proporcionar una lista de canciones con un browseId.
    # YouTube Music permite consultar ese browseId con get_playlist().
    # ------------------------------------------------------------
    if not canciones:
        bloque_canciones = datos.get("songs", {})
        songs_browse_id = bloque_canciones.get("browseId")

        if songs_browse_id:
            try:
                playlist = ytmusic.get_playlist(
                    songs_browse_id,
                    limit=None,
                )

                tracks = playlist.get("tracks", [])

                if tracks:
                    print(
                        f"Fuente nueva -> Songs fallback: "
                        f"{len(tracks)} canciones"
                    )

                for indice, track in enumerate(tracks):
                    video_id = track.get("videoId")
                    titulo = track.get("title")

                    if not video_id or not titulo:
                        continue

                    cancion_id = f"video:{video_id}"

                    if cancion_id in canciones_procesadas:
                        continue

                    artistas = extraer_artistas_de_objetos(
                        track.get("artists")
                    )

                    if not artistas:
                        artista_track = track.get("artist")
                        if artista_track:
                            artistas = [artista_track]

                    if not artistas:
                        artistas = [nombre]

                    track_para_cancion = dict(track)
                    track_para_cancion["videoId"] = video_id
                    track_para_cancion["title"] = titulo
                    track_para_cancion["artists"] = [
                        {"name": artista_nombre}
                        for artista_nombre in artistas
                    ]

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
                print(
                    f"ERROR en Songs fallback para {nombre} "
                    f"({channel_id}): {error}"
                )

    return canciones


def buscar_lanzamientos_adicionales_por_artista(
    ytmusic,
    artista,
    canciones_procesadas,
):
    """
    Fallback complementario para detectar lanzamientos que YouTube Music
    no exponga en las secciones habituales del canal.

    La búsqueda se hace por el artista monitorizado y solamente se aceptan
    resultados donde el artista aparezca realmente entre los artistas
    acreditados del resultado.

    No sustituye los canales configurados: añade una segunda vía de detección.
    """

    nombre = str(artista.get("nombre") or "").strip()
    if not nombre:
        return []

    consultas = [
        nombre,
        f"{nombre} 2026",
    ]

    artista_normalizado = normalizar_nombre(nombre)
    encontrados = {}

    print(
        f"Búsqueda adicional por artista: {nombre}"
    )

    for consulta in consultas:
        try:
            resultados = ytmusic.search(
                consulta,
                filter="songs",
                limit=20,
                ignore_spelling=True,
            )
        except Exception as error:
            print(
                f"  ERROR en búsqueda adicional '{consulta}': {error}"
            )
            continue

        for posicion, resultado in enumerate(resultados):
            if not isinstance(resultado, dict):
                continue

            video_id = resultado.get("videoId")
            titulo = resultado.get("title")
            if not video_id or not titulo:
                continue

            cancion_id = f"video:{video_id}"
            if cancion_id in canciones_procesadas:
                continue
            if video_id in encontrados:
                continue

            artistas_resultado = extraer_artistas_de_objetos(
                resultado.get("artists")
            )
            claves_resultado = {
                normalizar_nombre(x)
                for x in artistas_resultado
                if x
            }

            # El artista monitorizado debe aparecer de forma explícita.
            if artista_normalizado not in claves_resultado:
                continue

            album_resultado = resultado.get("album")
            album_id = None
            titulo_album = None
            if isinstance(album_resultado, dict):
                album_id = (
                    album_resultado.get("id")
                    or album_resultado.get("browseId")
                )
                titulo_album = (
                    album_resultado.get("name")
                    or album_resultado.get("title")
                )

            encontrados[video_id] = {
                "resultado": resultado,
                "album_id": album_id,
                "titulo_album": titulo_album,
                # Los primeros resultados reciben prioridad dentro del
                # fallback cuando se aplica la regla "solo la última".
                "orden_fallback": 100000 - posicion,
            }

    nuevas = []

    for video_id, datos in encontrados.items():
        resultado = datos["resultado"]
        album_id = datos["album_id"]
        titulo_album = datos["titulo_album"]

        anio = str(resultado.get("year") or "")

        # Si el año no viene en search(), intentamos obtenerlo desde el
        # álbum exacto ya identificado. Esto además valida que el album.id
        # siga siendo utilizable para la portada posterior.
        datos_album = None
        if album_id:
            try:
                datos_album = ytmusic.get_album(album_id)
            except Exception:
                datos_album = None

            if datos_album:
                anio = str(datos_album.get("year") or anio)
                titulo_album = (
                    datos_album.get("title")
                    or titulo_album
                )

        artistas = extraer_artistas_de_objetos(
            resultado.get("artists")
        )

        cancion = crear_cancion_desde_track(
            {
                "videoId": video_id,
                "title": resultado.get("title"),
                "artists": [
                    {"name": nombre_artista}
                    for nombre_artista in artistas
                ],
            },
            nombre,
            "Single",
            anio,
            titulo_lanzamiento=(titulo_album or resultado.get("title")),
            album_browse_id=album_id,
        )

        if not cancion:
            continue

        # El fallback es complementario a las fuentes de canal. Si la fuente
        # ya tiene una regla especial de primera integración, esa regla se
        # conserva para las canciones descubiertas por esta vía.
        cancion["_canal_origen"] = artista.get(
            "channel_id"
        ) or f"artist-search:{nombre}"
        cancion["_orden_origen"] = datos["orden_fallback"]
        cancion["_fuente_solo_ultima"] = bool(
            artista.get("solo_ultima_nueva", False)
            or artista.get("channels_solo_ultima_nueva")
        )
        cancion["_fuente_busqueda_adicional"] = True

        nuevas.append(cancion)

    if nuevas:
        print(
            f"  Búsqueda adicional -> {len(nuevas)} posible(s) lanzamiento(s)"
        )
    else:
        print(
            "  Búsqueda adicional -> sin candidatos nuevos"
        )

    return nuevas


def obtener_lanzamientos_artista(
    ytmusic,
    artista
):
    """
    Obtiene canciones individuales.

    Un artista puede tener uno o varios canales de YouTube Music.

    Single:
        1 canción.

    EP:
        Todas sus canciones.

    Álbum:
        Todas sus canciones.
    """

    nombre = artista["nombre"]

    # Mantiene compatibilidad con la estructura anterior:
    # si existe "channel_ids", se revisan todos;
    # si no, se usa el único "channel_id".
    channel_ids = artista.get("channel_ids")

    if not channel_ids:
        channel_id = artista.get("channel_id")

        if not channel_id:
            print(
                f"ERROR: {nombre} no tiene "
                f"ningún channel_id configurado."
            )
            return []

        channel_ids = [channel_id]

    print(
        f"Comprobando: {nombre}"
    )

    canciones = []

    # Evita duplicar la misma canción si aparece
    # en más de un canal del mismo artista.
    canciones_procesadas = set()

    # Evita llamar a get_album() dos veces para
    # lanzamientos equivalentes dentro del conjunto
    # de canales del artista.
    albumes_procesados = set()

    canales_solo_ultima = set(
        artista.get(
            "channels_solo_ultima_nueva",
            []
        )
    )

    artista_es_nuevo = bool(
        artista.get(
            "solo_ultima_nueva",
            False
        )
    )

    for numero_canal, channel_id in enumerate(
        channel_ids,
        start=1
    ):

        if len(channel_ids) > 1:
            print(
                f"  Canal {numero_canal}/"
                f"{len(channel_ids)}: "
                f"{channel_id}"
            )

        fuente_nueva = (
            artista_es_nuevo
            or channel_id in canales_solo_ultima
        )

        if fuente_nueva:
            canciones_nuevas = obtener_lanzamientos_fuente_nueva(
                ytmusic,
                channel_id,
                nombre,
                canciones_procesadas,
            )

            canciones.extend(canciones_nuevas)
            continue

        try:

            datos = ytmusic.get_artist(
                channel_id
            )

        except Exception as error:

            print(
                f"ERROR obteniendo "
                f"artista {nombre} "
                f"(canal {channel_id}): "
                f"{error}"
            )

            # Si un canal falla, se continúa con
            # los demás canales del mismo artista.
            continue

        # ========================================================
        # SINGLES
        # ========================================================

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

            cancion_id = f"video:{video_id}"

            # Si ya fue encontrada en otro canal,
            # no se vuelve a procesar.
            if cancion_id in canciones_procesadas:
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

            album_single = single.get("album")
            album_single_id = None
            if isinstance(album_single, dict):
                album_single_id = (
                    album_single.get("id")
                    or album_single.get("browseId")
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
                    },
                    nombre,
                    "Single",
                    anio,
                    titulo_lanzamiento=titulo,
                    album_browse_id=album_single_id,
                )
            )

            if cancion:

                cancion["_canal_origen"] = channel_id
                cancion["_orden_origen"] = len(canciones)
                cancion["_fuente_solo_ultima"] = (
                    artista_es_nuevo
                    or channel_id in canales_solo_ultima
                )

                canciones.append(
                    cancion
                )

                canciones_procesadas.add(
                    cancion_id
                )

        # ========================================================
        # EP / ÁLBUMES
        # ========================================================

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

            clave_album = (
                normalizar_titulo_album(
                    titulo_album
                ),
                normalizar_nombre(
                    tipo_album
                ),
                str(
                    album.get(
                        "year",
                        ""
                    )
                    or ""
                ).strip()
            )

            if clave_album in albumes_procesados:

                print(
                    f"Álbum equivalente omitido: "
                    f"{titulo_album}"
                )

                continue

            albumes_procesados.add(
                clave_album
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

            datos_album = (
                obtener_datos_album(
                    ytmusic,
                    browse_id
                )
            )

            if not datos_album:
                continue

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

                print(
                    f"Sin pistas disponibles: "
                    f"{titulo_album}"
                )

                continue

            print(
                f"{tipo_normalizado}: "
                f"{titulo_album} -> "
                f"{len(tracks)} canciones"
            )

            for track in tracks:

                video_id = track.get(
                    "videoId"
                )

                if not video_id:
                    continue

                cancion_id = f"video:{video_id}"

                if cancion_id in canciones_procesadas:
                    continue

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
                    )
                )

                if cancion:

                    cancion["_canal_origen"] = channel_id
                    cancion["_orden_origen"] = len(canciones)
                    cancion["_fuente_solo_ultima"] = (
                        artista_es_nuevo
                        or channel_id in canales_solo_ultima
                    )

                    canciones.append(
                        cancion
                    )

                    canciones_procesadas.add(
                        cancion_id
                    )

    return canciones


def _anio_numerico(cancion):
    """Convierte el año de una canción a entero para ordenar."""
    try:
        return int(str(cancion.get("anio") or "0").strip())
    except (TypeError, ValueError):
        return 0


def seleccionar_ultima_cancion(canciones):
    """Selecciona el lanzamiento más reciente de una fuente nueva."""
    if not canciones:
        return None

    # YouTube Music suele entregar los lanzamientos recientes primero.
    # El año refuerza la selección cuando el orden entre secciones difiere.
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


def preparar_nuevas_fuentes(
    canciones,
    canciones_publicadas,
):
    """
    Para cada fuente configurada como nueva:
    - deja solamente su lanzamiento más reciente para publicar;
    - registra como histórico todo lo anterior, evitando que se publique
      en ejecuciones posteriores;
    - cuando pase la primera integración, la fuente vuelve a funcionar
      normalmente porque lo anterior ya quedó registrado.
    """

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
# ALERTAS
# ============================================================

def enviar_alerta_error(
    cancion,
    etapa,
    detalle
):
    """
    Envía una alerta privada cuando
    una publicación falla.
    """

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
# PUBLICAR CANCIÓN
# ============================================================

def obtener_album_browse_id_para_cancion(ytmusic, cancion):
    """Resuelve el album/browse ID necesario para obtener la portada con get_album()."""
    album_browse_id = cancion.get("album_browse_id")
    if album_browse_id:
        return album_browse_id

    titulo = str(cancion.get("titulo") or "").strip()
    video_id = str(cancion.get("video_id") or "").strip()
    artistas_texto = str(cancion.get("artistas") or "").strip()

    if not titulo:
        return None

    consultas = []
    if artistas_texto:
        primer_artista = artistas_texto.split(",")[0].strip()
        if primer_artista:
            consultas.append(f"{titulo} {primer_artista}")
    consultas.append(titulo)

    vistas = set()
    for consulta in consultas:
        clave = consulta.casefold()
        if clave in vistas:
            continue
        vistas.add(clave)

        try:
            resultados = ytmusic.search(
                consulta,
                filter="songs",
                limit=20,
                ignore_spelling=True,
            )
        except Exception as error:
            print(f"No se pudo resolver album.id para '{titulo}': {error}")
            continue

        for resultado in resultados:
            if not isinstance(resultado, dict):
                continue
            if video_id:
                if resultado.get("videoId") != video_id:
                    continue
            elif str(resultado.get("title") or "").strip().casefold() != titulo.casefold():
                continue

            album = resultado.get("album")
            if not isinstance(album, dict):
                continue

            album_id = album.get("id") or album.get("browseId")
            if album_id:
                return album_id

    if video_id:
        try:
            lista = ytmusic.get_watch_playlist(
                videoId=video_id,
                limit=1,
            )
            for pista in (lista.get("tracks") or []):
                if pista.get("videoId") != video_id:
                    continue
                album = pista.get("album")
                if isinstance(album, dict):
                    album_id = album.get("id") or album.get("browseId")
                    if album_id:
                        return album_id
        except Exception as error:
            print(
                f"No se pudo resolver album.id con get_watch_playlist "
                f"para '{titulo}': {error}"
            )

    return None


def enviar_sin_portada(caption, reply_markup):
    """Publica solo texto con el botón cuando no hay portada disponible."""
    try:
        respuesta = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": "true",
                "reply_markup": json.dumps(
                    reply_markup,
                    ensure_ascii=False,
                ),
            },
            timeout=60,
        )
        if not respuesta.ok:
            return False, respuesta.text
        datos = respuesta.json()
        if not datos.get("ok"):
            return False, str(datos)
        return True, None
    except Exception as error:
        return False, str(error)


def _titulo_base(titulo):
    """Quita (feat. ...), [..] y similares para comparar títulos."""
    texto = re.sub(r"\s*[\(\[].*?[\)\]]", "", str(titulo or ""))
    return normalizar_titulo_album(texto)


def buscar_preview_deezer(cancion):
    """
    Busca en Deezer la canción y devuelve los datos de su preview
    de 30 segundos, o None si no hay una coincidencia fiable.
    """
    artistas_texto = str(cancion.get("artistas") or "").strip()
    titulo = str(cancion.get("titulo") or "").strip()
    if not artistas_texto or not titulo:
        return None

    primer_artista = artistas_texto.split(",")[0].strip()
    artista_norm = normalizar_titulo_album(primer_artista)
    titulo_norm = _titulo_base(titulo)
    titulo_limpio = re.sub(r"\s*[\(\[].*?[\)\]]", "", titulo).strip()

    consultas = [
        f'artist:"{primer_artista}" track:"{titulo_limpio}"',
        f"{primer_artista} {titulo_limpio}",
    ]

    for consulta in consultas:
        try:
            respuesta = requests.get(
                "https://api.deezer.com/search",
                params={"q": consulta, "limit": 10},
                timeout=20,
            )
            respuesta.raise_for_status()
            resultados = respuesta.json().get("data") or []
        except Exception as error:
            print(f"Preview: no se pudo consultar Deezer: {error}")
            continue

        for resultado in resultados:
            if not isinstance(resultado, dict):
                continue
            preview = resultado.get("preview")
            if not preview:
                continue
            if _titulo_base(resultado.get("title")) != titulo_norm:
                continue
            artista_resultado = normalizar_titulo_album(
                (resultado.get("artist") or {}).get("name")
            )
            if not artista_resultado:
                continue
            if (
                artista_norm == artista_resultado
                or artista_norm in artista_resultado
                or artista_resultado in artista_norm
            ):
                return {
                    "url": preview,
                    "titulo": resultado.get("title") or titulo,
                    "artista": (resultado.get("artist") or {}).get("name")
                    or primer_artista,
                }

    return None


def enviar_preview_audio(cancion):
    """
    Envía el adelanto de 30 s como audio justo debajo de la publicación.
    Nunca lanza errores ni afecta al estado: si falla, solo lo informa.
    """
    try:
        preview = buscar_preview_deezer(cancion)
        if not preview:
            print("Preview: sin coincidencia en Deezer; no se envía audio.")
            return False

        audio = requests.get(preview["url"], timeout=30)
        audio.raise_for_status()

        respuesta = requests.post(
            f"{TELEGRAM_API}/sendAudio",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "title": str(cancion.get("titulo") or preview["titulo"]),
                "performer": str(
                    cancion.get("artistas") or preview["artista"]
                ),
                "caption": "🎧 Adelanto de 30 s · vía Deezer",
                "duration": 30,
                "reply_markup": json.dumps(
                    {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "▶️ Escuchar en YouTube Music",
                                    "url": cancion["youtube_url"],
                                }
                            ]
                        ]
                    },
                    ensure_ascii=False,
                ),
            },
            files={
                "audio": (
                    f"{cancion.get('video_id') or 'preview'}.mp3",
                    BytesIO(audio.content),
                    "audio/mpeg",
                )
            },
            timeout=60,
        )
        if not respuesta.ok:
            print(f"Preview: Telegram rechazó el audio: {respuesta.text}")
            return False

        print("Preview de 30 s enviado correctamente.")
        return True
    except Exception as error:
        print(f"Preview: no se pudo enviar el audio: {error}")
        return False


def publicar_cancion(
    ytmusic,
    cancion
):
    """
    Publica una canción.

    Formato:

    🎤 Artistas
    🎵 Título
    📀 Nombre del EP/Álbum o Single
    🗓 2026

    @Cubaton_Music
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

    # ========================================================
    # FORMATO EXACTO DE PUBLICACIÓN
    # ========================================================

    caption = (
        f"🎤 <b>{artistas}</b>\n"
        f"<blockquote>🎵 <b>{titulo}</b></blockquote>\n"
        f"📀 <i>{nombre_publicacion}</i>\n"
        f"🗓 {anio}\n"
        f"\n"
        f"@Cubaton_Music"
    )

    # ========================================================
    # BOTÓN
    # ========================================================

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

    # ========================================================
    # PORTADA DE YOUTUBE MUSIC MEDIANTE EL ALBUM ID
    # ========================================================

    video_id = cancion[
        "video_id"
    ]

    album_browse_id = obtener_album_browse_id_para_cancion(
        ytmusic,
        cancion,
    )

    if not album_browse_id:
        if PUBLICAR_SIN_PORTADA_SI_FALLA:
            print(
                "AVISO: no se pudo identificar el album.id; "
                "se publica sin portada."
            )
            return enviar_sin_portada(caption, reply_markup)
        return (
            False,
            "No se pudo identificar el album.id de la canción; "
            "no se puede obtener la portada mediante get_album()."
        )

    try:
        print(
            f"Obteniendo portada desde YouTube Music mediante get_album(): "
            f"{album_browse_id}"
        )

        datos_album = ytmusic.get_album(
            album_browse_id
        )

        if not datos_album:
            return (
                False,
                f"get_album() no devolvió datos para {album_browse_id}."
            )

        thumbnails = datos_album.get("thumbnails") or []

        if not thumbnails:
            return (
                False,
                f"El álbum {album_browse_id} no contiene thumbnails."
            )

        # Seleccionar la miniatura de mayor resolución declarada por
        # YouTube Music, sin fabricar ni alterar la URL.
        thumbnails_validas = [
            thumbnail
            for thumbnail in thumbnails
            if isinstance(thumbnail, dict) and thumbnail.get("url")
        ]

        if not thumbnails_validas:
            return (
                False,
                f"El álbum {album_browse_id} no contiene thumbnails válidas."
            )

        portada = max(
            thumbnails_validas,
            key=lambda thumbnail: (
                int(thumbnail.get("width") or 0),
                int(thumbnail.get("height") or 0),
            ),
        )

        thumbnail_url = portada["url"]
        ancho_declarado = portada.get("width")
        alto_declarado = portada.get("height")

        print(
            f"Portada seleccionada: {ancho_declarado}x{alto_declarado}"
        )
        print(
            f"URL de YouTube Music: {thumbnail_url}"
        )

        imagen_respuesta = requests.get(
            thumbnail_url,
            timeout=30,
        )
        imagen_respuesta.raise_for_status()

        # Se envían exactamente los bytes de la imagen entregada por
        # YouTube Music. No se redimensiona, recorta ni recomprime.
        buffer = BytesIO(imagen_respuesta.content)
        buffer.seek(0)

        imagen = Image.open(buffer)
        print(
            f"Dimensiones reales descargadas: {imagen.width}x{imagen.height}"
        )
        print(
            f"Formato real descargado: {imagen.format}"
        )
        print(
            "La portada NO será redimensionada, recortada ni recomprimida."
        )

        buffer.seek(0)

    except Exception as error:
        return (
            False,
            f"No se pudo preparar la portada de YouTube Music mediante get_album(): {error}"
        )

    # ========================================================
    # ENVIAR A TELEGRAM
    # ========================================================

    try:
        respuesta = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(
                    reply_markup,
                    ensure_ascii=False,
                ),
            },
            files={
                "photo": (
                    f"{video_id}.jpg",
                    buffer,
                    "image/jpeg",
                )
            },
            timeout=60,
        )

        if not respuesta.ok:
            return (
                False,
                respuesta.text
            )

        datos = respuesta.json()

        if not datos.get("ok"):
            return (
                False,
                str(datos)
            )

        return (
            True,
            None
        )

    except Exception as error:
        return (
            False,
            str(error)
        )


# ============================================================
# CREAR LÍNEA BASE
# ============================================================

def crear_linea_base(
    ytmusic
):
    """
    Crea la línea base del nuevo sistema.

    IMPORTANTE:
    No publica nada.

    Registra cada canción individual.
    """

    print()
    print(
        "CREANDO NUEVA LÍNEA BASE"
    )

    print(
        "Sistema de seguimiento "
        "por canciones."
    )

    print(
        "No se publicará ningún "
        "lanzamiento."
    )

    print()

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
    print(
        "=" * 60
    )

    print(
        "LÍNEA BASE CREADA "
        "CORRECTAMENTE"
    )

    print(
        f"Canciones registradas: "
        f"{total_canciones}"
    )

    print(
        "No se publicó ninguna "
        "canción."
    )

    print(
        "A partir de la próxima "
        "ejecución se detectarán "
        "las nuevas canciones."
    )

    print(
        "=" * 60
    )

    return estado


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print(
        "=" * 60
    )

    print(
        "CUBATON MUSIC BOT"
    )

    print(
        "Detector automático "
        "de nuevas canciones"
    )

    print(
        "Singles + EP + Álbumes"
    )

    print(
        "=" * 60
    )

    if not TELEGRAM_BOT_TOKEN:

        print(
            "ERROR: No existe el secreto "
            "TELEGRAM_BOT_TOKEN."
        )

        raise SystemExit(1)

    # Verificar que el token sea válido antes de continuar.
    try:
        respuesta_token = requests.get(
            f"{TELEGRAM_API}/getMe",
            timeout=30,
        )
    except Exception as error:
        print(
            "ERROR: No se pudo contactar con Telegram "
            f"para validar el token: {error}"
        )
        raise SystemExit(1)

    if not respuesta_token.ok:
        print(
            "ERROR: TELEGRAM_BOT_TOKEN no es válido "
            f"({respuesta_token.status_code})."
        )
        raise SystemExit(1)

    ytmusic = YTMusic()

    # ========================================================
    # CARGAR ESTADO
    # ========================================================

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

    print()

    print(
        "Canciones registradas "
        "actualmente: "
        f"{len(canciones_publicadas)}"
    )

    print()

    # ========================================================
    # DETECTAR NUEVAS CANCIONES
    # ========================================================

    tamano_estado_inicial = len(canciones_publicadas)

    nuevas_canciones = []

    detectadas_en_esta_ejecucion = (
        set()
    )

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

        # --------------------------------------------------------
        # FALLBACK DE BÚSQUEDA POR ARTISTA
        # --------------------------------------------------------
        # Si las fuentes habituales no contienen novedades, existe un
        # fallback complementario por artista. Por seguridad permanece
        # desactivado hasta completar una validación controlada, porque
        # una búsqueda general puede devolver catálogo histórico.
        ids_habituales_nuevos = any(
            cancion.get("id") not in canciones_publicadas
            for cancion in canciones
            if cancion.get("id")
        )

        if (
            ACTIVAR_BUSQUEDA_ADICIONAL_POR_ARTISTA
            and not ids_habituales_nuevos
        ):
            canciones_fallback = buscar_lanzamientos_adicionales_por_artista(
                ytmusic,
                artista,
                canciones_procesadas={
                    cancion.get("id")
                    for cancion in canciones
                    if cancion.get("id")
                },
            )
            canciones.extend(canciones_fallback)
        elif not ids_habituales_nuevos:
            print(
                "  Búsqueda adicional por artista: DESACTIVADA "
                "(modo seguro)"
            )

        # Registra la clave (artista + título) de las canciones ya
        # conocidas, para reconocerlas si reaparecen con otro ID.
        for cancion in canciones:
            if cancion.get("id") in canciones_publicadas:
                canciones_publicadas.add(clave_cancion(cancion))

        # Para artistas nuevos o canales nuevos configurados con la regla
        # "solo la última", los lanzamientos anteriores se registran como
        # históricos y solamente el más reciente queda disponible para
        # publicación.
        canciones = preparar_nuevas_fuentes(
            canciones,
            canciones_publicadas,
        )

        for cancion in canciones:

            cancion_id = cancion[
                "id"
            ]

            # Ya publicada
            if (
                cancion_id
                in canciones_publicadas
            ):
                continue

            # Duplicada en esta ejecución
            if (
                cancion_id
                in detectadas_en_esta_ejecucion
            ):
                continue

            clave = clave_cancion(cancion)

            # Misma canción con otro ID (single/álbum/video)
            if (
                clave in canciones_publicadas
                or clave in detectadas_en_esta_ejecucion
            ):
                print(
                    "  Omitida (misma canción con otro ID): "
                    f"{cancion['titulo']}"
                )
                canciones_publicadas.add(cancion_id)
                continue

            # Demasiado antigua: se registra como histórica
            anio_numero = _anio_numerico(cancion)
            anio_limite = (
                datetime.now(timezone.utc).year
                - MAX_ANTIGUEDAD_ANIOS
            )
            if anio_numero and anio_numero < anio_limite:
                print(
                    f"  Omitida (año {anio_numero}, antigua): "
                    f"{cancion['titulo']}"
                )
                canciones_publicadas.add(cancion_id)
                canciones_publicadas.add(clave)
                continue

            detectadas_en_esta_ejecucion.add(
                cancion_id
            )
            detectadas_en_esta_ejecucion.add(
                clave
            )

            nuevas_canciones.append(
                cancion
            )

    # Guarda lo registrado como histórico o duplicado en esta ejecución
    if len(canciones_publicadas) != tamano_estado_inicial:
        guardar_estado(estado)

    # ========================================================
    # RESULTADO DEL DETECTOR
    # ========================================================

    print()

    if not nuevas_canciones:

        print(
            "No se detectaron "
            "canciones nuevas."
        )

        print(
            "No hay nada que publicar."
        )

        return

    print(
        f"Se detectaron "
        f"{len(nuevas_canciones)} "
        "canción(es) nueva(s)."
    )

    print()

    # ========================================================
    # PUBLICAR
    # ========================================================

    publicadas = 0
    errores = 0

    for numero, cancion in enumerate(
        nuevas_canciones,
        start=1
    ):

        print(
            f"[PUBLICACIÓN "
            f"{numero}/"
            f"{len(nuevas_canciones)}]"
        )

        print(
            f"Artista(s): "
            f"{cancion['artistas']}"
        )

        print(
            f"Canción: "
            f"{cancion['titulo']}"
        )

        print(
            f"Lanzamiento: "
            f"{cancion['nombre_publicacion']}"
        )

        print(
            f"Año: "
            f"{cancion['anio']}"
        )

        exito, error = (
            publicar_cancion(
                ytmusic,
                cancion
            )
        )

        if exito:

            print(
                "PUBLICADA "
                "CORRECTAMENTE"
            )

            # Solo se registra después
            # de confirmarse la publicación.
            canciones_publicadas.add(
                cancion["id"]
            )
            canciones_publicadas.add(
                clave_cancion(cancion)
            )

            # Guardado inmediato.
            guardar_estado(
                estado
            )

            publicadas += 1

            # Adelanto de audio justo debajo de la publicación.
            if ENVIAR_PREVIEW_AUDIO:
                enviar_preview_audio(cancion)

        else:

            print(
                "ERROR AL PUBLICAR"
            )

            print(
                error
            )

            errores += 1

            enviar_alerta_error(
                cancion,
                "Publicación en Telegram",
                error,
            )

            # No se registra.
            # Se reintentará en la próxima
            # ejecución.

        print()

    # ========================================================
    # RESUMEN
    # ========================================================

    print(
        "=" * 60
    )

    print(
        "RESUMEN DE LA EJECUCIÓN"
    )

    print(
        f"Nuevas detectadas: "
        f"{len(nuevas_canciones)}"
    )

    print(
        f"Publicadas: "
        f"{publicadas}"
    )

    print(
        f"Errores: "
        f"{errores}"
    )

    print(
        "Total registradas en estado: "
        f"{len(canciones_publicadas)}"
    )

    print(
        "=" * 60
    )

    if errores > 0:
        raise SystemExit(1)


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":
    main()
