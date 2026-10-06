import os
import re
import time
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

# No se publican canciones cuyo año sea anterior al año actual menos este
# valor (1 = solo año actual y anterior). Las descartadas se registran como
# históricas. Para pruebas con canciones antiguas, súbelo temporalmente.
MAX_ANTIGUEDAD_ANIOS = 1

# Si no se logra resolver el álbum para obtener la portada, publicar la
# canción solo con texto y botón (True) en lugar de reintentar y enviar
# una alerta en cada ejecución (False).
PUBLICAR_SIN_PORTADA_SI_FALLA = True

# Envía debajo de cada publicación un adelanto de unos 30 segundos
# (preview oficial para promoción: Apple Music y, como respaldo, Deezer). Si no se encuentra
# la canción o falla el envío, simplemente no se envía y no se genera alerta.
ENVIAR_PREVIEW_AUDIO = True

# Botón "Escuchar en YouTube Music" en el post principal. Con False solo
# aparece en el post cuando no hay preview de audio; el preview lo lleva siempre.
BOTON_EN_POST = False

# Pausa (segundos) tras cada pareja Post + Audio, para no superar los
# límites de envío de Telegram al publicar varias canciones seguidas.
PAUSA_ENTRE_PUBLICACIONES = 2

# Busca canciones donde participa un artista monitorizado pero que están en
# el canal de otro artista (colaboraciones). Solo se consideran las del año
# actual; las de años anteriores se registran como históricas. La primera vez
# que se busca para cada artista, todo lo encontrado se registra sin publicar.
BUSCAR_COLABORACIONES = True

# Detecta lanzamientos nuevos también en Deezer (suelen llegar antes que a
# YouTube Music). Requiere "deezer_id" en cada artista. La primera vez que se
# lee cada artista, todo lo existente se registra sin publicar.
BUSCAR_EN_DEEZER = True
DEEZER_API = "https://api.deezer.com"

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
        "deezer_id": "102097852",
        "channel_id": "UCpVfWS-cPOE2sYqsFuuP_Qg",
    },
    {
        "nombre": "Charly & Johayron",
        "deezer_id": "151878182",
        "channel_id": "UCnwEtOQyXJUUuBhcTgImdfQ",
    },
    {
        "nombre": "Dany Ome",
        "deezer_id": "51312522",
        "channel_id": "UCJQEm9t4KjDn-I8Fahf4Uqw",
    },
    {
        "nombre": "Wampi",
        "deezer_id": "53583382",
        "channel_id": "UCbfzw8u1lCwDMv443StJEOw",
    },
    {
        "nombre": "El Taiger",
        "deezer_id": "10733244",
        "channel_id": "UCoYtt7bGCV5RyUweyQgqQ4A",
    },
    {
        "nombre": "Ja Rulay",
        "deezer_id": "141683852",
        "channel_id": "UCcaU4COep7mj8kbXwS24JFQ",
    },
    {
        "nombre": "L Kimii",
        "deezer_id": "166612297",
        "channel_id": "UCMyQosiL8iVUtXPIm1UZJQg",
    },
    {
        "nombre": "El Dray",
        "deezer_id": "14445985",
        "channel_id": "UC4kpn8y8QXYXmyDn8HJKD8Q",
    },
    {
        "nombre": "Mauro y El Pitu",
        "deezer_id": "233465501",
        "channel_id": "UCvN1mRFfAfWYTiIkM70qUWA",
    },
    {
        "nombre": "Yirow Y El Tingo",
        "deezer_id": "246706542",
        "channel_id": "UCEq3_5h1Xi_vLbytP7OzuNA",
    },
    {
        "nombre": "Nany La Kbra",
        "deezer_id": "349727462",
        "channel_id": "UCG4lSNdNx_LuLnN2EW6uWwQ",
    },
    {
        "nombre": "Ya Ice Dilan",
        "deezer_id": "312201361",
        "channel_id": "UC9aJbR9Q8nscvZaMw_cH4Ww",
    },
    {
        "nombre": "Rey Tony",
        "deezer_id": "11269534",
        "channel_id": "UCDhExL0uVtumv_DEjPPq5qg",
    },
    {
        "nombre": "Baby Maikol",
        "deezer_id": "95702072",
        "channel_id": "UCP5R6Mgbk_bgtgzZguLNKdA",
    },
    {
        "nombre": "Payaso X Ley",
        "deezer_id": "100735422",
        "channel_id": "UCauTaqBvFqqqJTu3B4Wc1GA",
    },
    {
        "nombre": "Kaly Y Kowa",
        "deezer_id": "268432602",
        "channel_id": "UCSfR51myQhs2ZcdzrWo0Z4w",
    },
    {
        "nombre": "Wildey",
        "deezer_id": "8440220",
        "channel_id": "UCmFS-VSa4Wf3F1wdWS-8p_g",
    },
    {
        "nombre": "Wow Popy",
        "deezer_id": "94339592",
        "channel_id": "UCtFkN8UFxT_MuNdySlfuFuA",
    },
    {
        "nombre": "Talent Fuego",
        "deezer_id": "319839381",
        "channel_id": "UC0dVmcXfNa7lVeUBve3_FXw",
    },
    {
        "nombre": "Mawell",
        "deezer_id": "11269890",
        "channel_id": "UCL6P-jUDZEKBA-Lb6WFccWg",
    },
    {
        "nombre": "Harryson",
        "deezer_id": "305498",
        "channel_id": "UC2ihX5uoblnN4wsA-ayIAAA",
    },
    {
        "nombre": "El Chulo",
        "deezer_id": "1318293",
        "channel_id": "UCiT8VNdnpeYnCTPJZoqym9g",
    },
    {
        "nombre": "Fixty Ordara",
        "deezer_id": "148250982",
        "channel_id": "UCDHDCbVOQywsLCsCZ8PH-AA",
    },
    {
        "nombre": "El Kamel",
        "deezer_id": "13147221",
        "channel_id": "UCPnWcazEV7QM0H7qBx6NVXg",
    },
    {
        "nombre": "Velito el Bufón",
        "deezer_id": "154487672",
        "channel_id": "UCRA9cRfAJXuxDRcFnoB7pwg",
    },
    {
        "nombre": "Un Titico",
        "deezer_id": "14576461",
        "channel_id": "UCT2KiGFSPZIF3DR9UIN2fYw",
    },
    {
        "nombre": "Musteerifa",
        "deezer_id": "297753211",
        "channel_id": "UCiT8PzlQqtPC7lWFh3--4jw",
        "channel_ids": [
            "UCiT8PzlQqtPC7lWFh3--4jw",
            "UCUmbJ10w6Sljv-zIv0iQxNw",
        ],
    },
    {
        "nombre": "Los Dele",
        "deezer_id": "246797622",
        "channel_id": "UCe9SuCBefzhTyPCgiMMvcbA",
    },
    {
        "nombre": "Chocolate MC",
        "deezer_id": "1385931",
        "channel_id": "UCYVuThmAmbXxk1o9Un5Cc_w",
    },
    {
        "nombre": "El Chacal",
        "deezer_id": "357494",
        "channel_id": "UCJt4IsSmUjqTaamhCJoKK_g",
    },
    {
        "nombre": "El Micha",
        "deezer_id": "279482",
        "channel_id": "UCHhrMSqe_C1E_JBEz3mRlew",
    },
    {
        "nombre": "Yomil",
        "deezer_id": "5051695",
        "channel_id": "UCPfXwOpwRIbVsqqTsgt4i5g",
    },
    {
        "nombre": "Jacob Forever",
        "deezer_id": "1533735",
        "channel_id": "UCJ1-Pwsroy-gzMqlfKDF4Hg",
    },
    {
        "nombre": "Gente de Zona",
        "deezer_id": "279489",
        "channel_id": "UCl2KQVc_GFH081i7b9CJQug",
    },
    {
        "nombre": "La Diosa",
        "deezer_id": "4266566",
        "channel_id": "UChbVOQHgq01JoHY4axuWV0A",
    },
    {
        "nombre": "Seidy La Niña",
        "deezer_id": "59734012",
        "channel_id": "UCFqYfgj_7h3ZUkBnyYS-TFg",
    },
    {
        "nombre": "Yandito",
        "deezer_id": "104387432",
        "channel_id": "UCDBIl4Gc9VJjTSy8g_tve5w",
        "channel_ids": [
            "UCDBIl4Gc9VJjTSy8g_tve5w",
            "UCcXUh7Nrgx2uDJxBrgj5XMQ",
        ],
    },
    {
        "nombre": "Yeyito DK",
        "deezer_id": "262957411",
        "channel_id": "UCrP6x4goKf26TaWWHbJM0ZA",
        "channel_ids": [
            "UCrP6x4goKf26TaWWHbJM0ZA",
            "UCwOsxuuwyt--PMDxAXdYYLQ",
            "UCcr2yCU1UnvRIomc56WxFgA",
        ],
    },
    # Estos se configuran por @usuario; el bot obtiene su channel_id
    # al arrancar (ver resolver_handles_artistas).
    {
        "nombre": "Anyelazo",
        "deezer_id": "262524691",
        "handle": "@anyelazo_oficial",
    },
    {
        "nombre": "El Yohas",
        "deezer_id": "269045212",
        "handle": "@el_yohas",
    },
    {
        "nombre": "El Ankla",
        "deezer_id": "64307332",
        "handle": "@elanklaofficial",
    },
    {
        "nombre": "Dj Honda",
        "handle": "@hondadj2026",
    },
    # Artista solo con Deezer (sin canal de YouTube Music configurado).
    {
        "nombre": "Ozunaje",
        "deezer_id": "298508751",
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

def _titulo_sin_feat(titulo):
    """Título normalizado sin '(feat. ...)' / '(with ...)'."""
    texto = re.sub(
        r"\s*[\(\[]\s*(?:feat|ft|featuring|with)\b[^\)\]]*[\)\]]",
        "",
        str(titulo or ""),
        flags=re.IGNORECASE,
    )
    return normalizar_titulo_album(texto)


def clave_base_cancion(cancion):
    """
    Clave entre fuentes (YouTube Music / Deezer): artista monitorizado +
    título sin feat. Evita publicar dos veces la misma canción.
    """
    monitorizado = normalizar_titulo_album(
        cancion.get("artista_monitorizado")
    )
    return f"m:{monitorizado}|{_titulo_sin_feat(cancion.get('titulo'))}"


def registrar_claves_cancion(canciones_publicadas, cancion):
    """Registra las dos claves de comparación de una canción."""
    canciones_publicadas.add(clave_cancion(cancion))
    canciones_publicadas.add(clave_base_cancion(cancion))


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

        if not channel_id and artista.get("deezer_id"):
            # Artista configurado solo con Deezer.
            return []

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
                **(
                    {
                        "reply_markup": json.dumps(
                            reply_markup,
                            ensure_ascii=False,
                        )
                    }
                    if reply_markup
                    else {}
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


def _datos_busqueda_preview(cancion):
    """Prepara artista y título normalizados para buscar previews."""
    artistas_texto = str(cancion.get("artistas") or "").strip()
    titulo = str(cancion.get("titulo") or "").strip()
    if not artistas_texto or not titulo:
        return None

    primer_artista = artistas_texto.split(",")[0].strip()
    titulo_limpio = re.sub(r"\s*[\(\[].*?[\)\]]", "", titulo).strip()
    return {
        "primer_artista": primer_artista,
        "titulo_limpio": titulo_limpio,
        "artista_norm": normalizar_titulo_album(primer_artista),
        "titulo_norm": _titulo_base(titulo),
    }


def _coincide_preview(titulo_resultado, artista_resultado, datos):
    """Exige que título y artista coincidan para evitar canciones erróneas."""
    if _titulo_base(titulo_resultado) != datos["titulo_norm"]:
        return False
    artista_res = normalizar_titulo_album(artista_resultado)
    if not artista_res:
        return False
    artista_norm = datos["artista_norm"]
    return (
        artista_norm == artista_res
        or artista_norm in artista_res
        or artista_res in artista_norm
    )


def buscar_preview_deezer(cancion):
    """Devuelve la URL del preview de 30 s en Deezer, o None."""
    datos = _datos_busqueda_preview(cancion)
    if not datos:
        return None

    consultas = [
        f'artist:"{datos["primer_artista"]}" track:"{datos["titulo_limpio"]}"',
        f'{datos["primer_artista"]} {datos["titulo_limpio"]}',
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
            if _coincide_preview(
                resultado.get("title"),
                (resultado.get("artist") or {}).get("name"),
                datos,
            ):
                return {"url": preview}

    return None


def buscar_preview_apple(cancion):
    """Devuelve la URL del preview de 30 s en Apple Music (iTunes), o None."""
    datos = _datos_busqueda_preview(cancion)
    if not datos:
        return None

    for pais in ("US", "ES"):
        try:
            respuesta = requests.get(
                "https://itunes.apple.com/search",
                params={
                    "term": f'{datos["primer_artista"]} {datos["titulo_limpio"]}',
                    "media": "music",
                    "entity": "song",
                    "limit": 15,
                    "country": pais,
                },
                timeout=20,
            )
            respuesta.raise_for_status()
            resultados = respuesta.json().get("results") or []
        except Exception as error:
            print(f"Preview: no se pudo consultar Apple Music ({pais}): {error}")
            continue

        for resultado in resultados:
            if not isinstance(resultado, dict):
                continue
            preview = resultado.get("previewUrl")
            if not preview:
                continue
            if _coincide_preview(
                resultado.get("trackName"),
                resultado.get("artistName"),
                datos,
            ):
                return {"url": preview}

    return None


def buscar_preview(cancion):
    """
    Busca el preview en Apple Music y, si falla, en Deezer.
    Descarga el audio de antemano. Devuelve un diccionario con el
    contenido o None si no hay preview disponible.
    """
    fuentes = (
        ("Apple Music", buscar_preview_apple, "m4a", "audio/mp4"),
        ("Deezer", buscar_preview_deezer, "mp3", "audio/mpeg"),
    )

    for nombre, funcion, extension, mime in fuentes:
        try:
            datos = funcion(cancion)
            if not datos:
                continue
            audio = requests.get(datos["url"], timeout=30)
            audio.raise_for_status()
            if not audio.content:
                continue
            print(f"Preview encontrado en {nombre}.")
            return {
                "bytes": audio.content,
                "extension": extension,
                "mime": mime,
                "fuente": nombre,
            }
        except Exception as error:
            print(f"Preview: fallo con {nombre}: {error}")

    print("Preview: sin coincidencia en Apple Music ni Deezer.")
    return None


def enviar_preview_audio(cancion, preview):
    """
    Envía el preview como audio justo debajo de la publicación.
    Nunca lanza errores ni afecta al estado: si falla, solo lo informa.
    Si Telegram pide esperar (error 429), espera y reintenta una vez.
    """
    teclado = json.dumps(
        _boton_cancion(cancion),
        ensure_ascii=False,
    )

    try:
        for intento in range(2):
            respuesta = requests.post(
                f"{TELEGRAM_API}/sendAudio",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "title": str(cancion.get("titulo") or ""),
                    "performer": str(cancion.get("artistas") or ""),
                    "duration": 30,
                    "reply_markup": teclado,
                },
                files={
                    "audio": (
                        f"{cancion.get('video_id') or 'preview'}."
                        f"{preview['extension']}",
                        BytesIO(preview["bytes"]),
                        preview["mime"],
                    )
                },
                timeout=60,
            )

            if respuesta.status_code == 429 and intento == 0:
                try:
                    espera = int(
                        respuesta.json()
                        .get("parameters", {})
                        .get("retry_after", 5)
                    )
                except Exception:
                    espera = 5
                espera = max(1, min(espera, 30))
                print(f"Preview: Telegram pide esperar {espera} s; reintentando.")
                time.sleep(espera)
                continue

            break

        if not respuesta.ok:
            print(f"Preview: Telegram rechazó el audio: {respuesta.text}")
            return False

        print(f"Preview de 30 s enviado correctamente ({preview['fuente']}).")
        return True
    except Exception as error:
        print(f"Preview: no se pudo enviar el audio: {error}")
        return False


def _boton_cancion(cancion):
    """Botón inline de la canción (YouTube Music por defecto)."""
    texto = cancion.get("boton_texto") or "▶️ Escuchar en YouTube Music"
    url = cancion.get("boton_url") or cancion.get("youtube_url")
    return {"inline_keyboard": [[{"text": texto, "url": url}]]}


def _publicar_con_portada_url(cancion, caption, reply_markup, con_boton):
    """Publica usando una portada ya disponible por URL (p. ej. Deezer)."""
    try:
        imagen = requests.get(cancion["portada_url"], timeout=30)
        imagen.raise_for_status()
        contenido = imagen.content
        if not contenido:
            raise ValueError("la portada descargada está vacía")
    except Exception as error:
        if PUBLICAR_SIN_PORTADA_SI_FALLA:
            print(f"AVISO: no se pudo descargar la portada ({error}); se publica sin portada.")
            return enviar_sin_portada(
                caption,
                reply_markup if con_boton else None,
            )
        return False, f"No se pudo descargar la portada: {error}"

    try:
        respuesta = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML",
                **(
                    {
                        "reply_markup": json.dumps(
                            reply_markup,
                            ensure_ascii=False,
                        )
                    }
                    if con_boton
                    else {}
                ),
            },
            files={
                "photo": (
                    f"{cancion.get('video_id') or 'portada'}.jpg",
                    BytesIO(contenido),
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
        return True, None
    except Exception as error:
        return False, str(error)


def publicar_cancion(
    ytmusic,
    cancion,
    con_boton=False,
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
        f"<b>@Cubaton_Music</b>"
    )

    # ========================================================
    # BOTÓN
    # ========================================================

    reply_markup = _boton_cancion(cancion)

    # ========================================================
    # PORTADA DE YOUTUBE MUSIC MEDIANTE EL ALBUM ID
    # ========================================================

    video_id = cancion[
        "video_id"
    ]

    # Canciones de otras fuentes (Deezer) traen su portada por URL.
    if cancion.get("portada_url"):
        return _publicar_con_portada_url(
            cancion,
            caption,
            reply_markup,
            con_boton,
        )

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
            return enviar_sin_portada(
                caption,
                reply_markup if con_boton else None,
            )
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
                **(
                    {
                        "reply_markup": json.dumps(
                            reply_markup,
                            ensure_ascii=False,
                        )
                    }
                    if con_boton
                    else {}
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

def ids_canales_monitorizados():
    """Conjunto con todos los channel_id de los artistas configurados."""
    ids = set()
    for artista in ARTISTAS:
        if artista.get("channel_id"):
            ids.add(artista["channel_id"])
        ids.update(artista.get("channel_ids") or [])
    return ids


def buscar_colaboraciones_artista(
    ytmusic,
    artista,
    ids_monitorizados,
    canciones_publicadas,
    albumes_cache,
):
    """
    Busca canciones donde aparece un artista monitorizado (por ID de canal,
    nunca por nombre) aunque estén en el canal de otro artista.
    Devuelve las canciones candidatas del año actual. Las de años anteriores,
    y todo lo encontrado en la primera pasada de cada artista, se registran
    como históricas.
    """
    if not (artista.get("channel_id") or artista.get("channel_ids")):
        return []

    nombre = artista["nombre"]
    marca_base = f"base:colab:{normalizar_nombre(nombre)}"
    primera_pasada = marca_base not in canciones_publicadas
    anio_actual = datetime.now(timezone.utc).year

    try:
        resultados = ytmusic.search(
            nombre,
            filter="songs",
            limit=40,
        )
    except Exception as error:
        print(f"  Colaboraciones: no se pudo buscar '{nombre}': {error}")
        return []

    candidatas = []
    registradas = 0

    for resultado in resultados or []:
        if not isinstance(resultado, dict):
            continue

        video_id = resultado.get("videoId")
        titulo = resultado.get("title")
        if not video_id or not titulo:
            continue

        cancion_id = f"video:{video_id}"
        if cancion_id in canciones_publicadas:
            continue

        artistas_resultado = [
            a
            for a in (resultado.get("artists") or [])
            if isinstance(a, dict)
        ]
        ids_resultado = {
            a.get("id") for a in artistas_resultado if a.get("id")
        }
        if not (ids_resultado & ids_monitorizados):
            continue

        album = resultado.get("album")
        album = album if isinstance(album, dict) else {}
        album_id = album.get("id")

        datos_album = None
        if album_id:
            if album_id in albumes_cache:
                datos_album = albumes_cache[album_id]
            else:
                try:
                    datos_album = ytmusic.get_album(album_id)
                except Exception as error:
                    print(
                        f"  Colaboraciones: no se pudo obtener el álbum "
                        f"{album_id}: {error}"
                    )
                    datos_album = None
                albumes_cache[album_id] = datos_album

        datos_album = datos_album if isinstance(datos_album, dict) else {}
        anio = datos_album.get("year") or resultado.get("year") or ""

        tipo = str(datos_album.get("type") or "Single").strip()
        if tipo.casefold() == "ep":
            tipo = "EP"
        elif tipo.casefold() in ("album", "álbum"):
            tipo = "Album"
        else:
            tipo = "Single"

        titulo_lanzamiento = (
            datos_album.get("title")
            or album.get("name")
            or titulo
        )

        cancion = crear_cancion_desde_track(
            {
                "videoId": video_id,
                "title": titulo,
                "artists": artistas_resultado,
            },
            nombre,
            tipo,
            anio,
            titulo_lanzamiento=titulo_lanzamiento,
            album_browse_id=album_id,
        )
        if not cancion:
            continue

        anio_numero = _anio_numerico(cancion)
        if not anio_numero:
            # Sin año fiable: no se publica ni se registra todavía.
            continue

        if primera_pasada or anio_numero != anio_actual:
            canciones_publicadas.add(cancion_id)
            registrar_claves_cancion(canciones_publicadas, cancion)
            registradas += 1
        else:
            candidatas.append(cancion)

    canciones_publicadas.add(marca_base)

    if primera_pasada:
        print(
            f"  Colaboraciones: primera pasada, {registradas} "
            f"registrada(s) como históricas."
        )
    elif candidatas or registradas:
        print(
            f"  Colaboraciones: {len(candidatas)} candidata(s), "
            f"{registradas} histórica(s)."
        )

    return candidatas


def _deezer_get(ruta, params=None):
    """GET a la API pública de Deezer. Devuelve el JSON o None si falla."""
    for intento in range(2):
        try:
            time.sleep(0.2)
            respuesta = requests.get(
                f"{DEEZER_API}{ruta}",
                params=params,
                timeout=20,
            )
            datos = respuesta.json()
        except Exception as error:
            print(f"  Deezer: error consultando {ruta}: {error}")
            return None

        if isinstance(datos, dict) and datos.get("error"):
            codigo = (datos["error"] or {}).get("code")
            if codigo == 4 and intento == 0:
                time.sleep(3)
                continue
            print(f"  Deezer: {ruta} devolvió error: {datos['error']}")
            return None

        return datos

    return None


def _albumes_deezer(deezer_id):
    """Lista los lanzamientos de un artista (hasta 300). None si falla."""
    albumes = []
    indice = 0
    for _ in range(3):
        datos = _deezer_get(
            f"/artist/{deezer_id}/albums",
            {"limit": 100, "index": indice},
        )
        if not isinstance(datos, dict):
            return None
        albumes.extend(datos.get("data") or [])
        if not datos.get("next"):
            break
        indice += 100
    return albumes


def _canciones_de_album_deezer(
    nombre,
    deezer_id,
    album_id,
    resumen,
    canciones_publicadas,
):
    """
    Convierte un álbum/EP/single de Deezer en canciones publicables.
    Solo incluye pistas donde participa el artista. Devuelve None si falla.
    """
    detalle = _deezer_get(f"/album/{album_id}")
    if not isinstance(detalle, dict):
        return None

    tipo_deezer = str(
        detalle.get("record_type") or resumen.get("record_type") or ""
    ).casefold()
    if tipo_deezer == "single":
        tipo = "Single"
    elif tipo_deezer == "ep":
        tipo = "EP"
    else:
        tipo = "Album"

    titulo_album = detalle.get("title") or resumen.get("title") or "Sin título"
    fecha = str(detalle.get("release_date") or resumen.get("release_date") or "")
    anio = fecha[:4]
    portada = (
        detalle.get("cover_xl")
        or detalle.get("cover_big")
        or resumen.get("cover_xl")
        or resumen.get("cover_big")
    )
    pistas = ((detalle.get("tracks") or {}).get("data")) or []

    resultado = []
    for pista in pistas:
        track_id = pista.get("id")
        if not track_id:
            continue
        cancion_id = f"deezer:{track_id}"
        if cancion_id in canciones_publicadas:
            continue

        detalle_pista = _deezer_get(f"/track/{track_id}")
        if not isinstance(detalle_pista, dict):
            return None

        contribuyentes = [
            c
            for c in (detalle_pista.get("contributors") or [])
            if isinstance(c, dict) and c.get("name")
        ]
        if not contribuyentes:
            contribuyentes = [pista.get("artist") or {"name": nombre}]

        ids_contribuyentes = {str(c.get("id")) for c in contribuyentes}
        if str(deezer_id) not in ids_contribuyentes:
            # Pista donde no participa el artista (p. ej. recopilatorios).
            canciones_publicadas.add(cancion_id)
            continue

        titulo = detalle_pista.get("title") or pista.get("title")
        if not titulo:
            continue

        resultado.append(
            {
                "id": cancion_id,
                "video_id": f"deezer{track_id}",
                "titulo": titulo,
                "artistas": formatear_artistas(
                    [c["name"] for c in contribuyentes]
                ),
                "tipo": tipo,
                "anio": anio,
                "nombre_publicacion": (
                    "Single" if tipo == "Single" else titulo_album
                ),
                "youtube_url": None,
                "boton_texto": "▶️ Escuchar en Deezer",
                "boton_url": (
                    detalle_pista.get("link")
                    or pista.get("link")
                    or detalle.get("link")
                ),
                "artista_monitorizado": nombre,
                "titulo_lanzamiento": titulo_album,
                "album_browse_id": None,
                "portada_url": portada,
                "fuente": "deezer",
            }
        )

    return resultado


def buscar_lanzamientos_deezer(artista, canciones_publicadas):
    """
    Detecta lanzamientos nuevos del año actual en Deezer.
    - Primera lectura de cada artista: registra todo sin publicar.
    - Después: solo lanzamientos del año actual, ya publicados en Deezer
      (fecha de hoy o anterior) y no vistos antes.
    """
    deezer_id = str(artista.get("deezer_id") or "").strip()
    if not deezer_id:
        return []

    nombre = artista["nombre"]
    marca_base = f"base:deezer:{deezer_id}"
    primera_pasada = marca_base not in canciones_publicadas

    albumes = _albumes_deezer(deezer_id)
    if albumes is None:
        print(f"  Deezer: no se pudo leer el catálogo de {nombre}.")
        return []

    hoy = datetime.now(timezone.utc).date()
    candidatas = []
    registrados = 0

    for album in albumes:
        if not isinstance(album, dict) or not album.get("id"):
            continue

        marca_album = f"deezer:album:{album['id']}"
        if marca_album in canciones_publicadas:
            continue

        if primera_pasada:
            canciones_publicadas.add(marca_album)
            registrados += 1
            continue

        try:
            fecha = datetime.strptime(
                str(album.get("release_date") or "")[:10],
                "%Y-%m-%d",
            ).date()
        except ValueError:
            continue

        if fecha > hoy:
            # Aún no ha salido: se revisa en una ejecución posterior.
            continue

        if fecha.year != hoy.year:
            canciones_publicadas.add(marca_album)
            registrados += 1
            continue

        canciones_album = _canciones_de_album_deezer(
            nombre,
            deezer_id,
            album["id"],
            album,
            canciones_publicadas,
        )
        if canciones_album is None:
            continue  # se reintenta en la próxima ejecución

        if canciones_album:
            candidatas.extend(canciones_album)
        else:
            canciones_publicadas.add(marca_album)

    canciones_publicadas.add(marca_base)

    if primera_pasada:
        print(
            f"  Deezer: primera lectura, {registrados} lanzamiento(s) "
            f"registrado(s) como históricos."
        )
    elif candidatas:
        print(f"  Deezer: {len(candidatas)} canción(es) candidata(s).")

    return candidatas


def resolver_handle_a_channel_id(handle):
    """
    Obtiene el channel_id (UC...) de un canal a partir de su @usuario.
    Devuelve None si no se logra; en ese caso el artista se omite.
    """
    handle = str(handle or "").strip()
    if not handle:
        return None
    if not handle.startswith("@"):
        handle = "@" + handle

    try:
        respuesta = requests.get(
            f"https://www.youtube.com/{handle}",
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Cookie": "CONSENT=YES+1; SOCS=CAI",
            },
            timeout=30,
        )
        respuesta.raise_for_status()
        texto = respuesta.text

        patrones = (
            r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})"',
            r'"externalId":"(UC[\w-]{22})"',
            r'"channelId":"(UC[\w-]{22})"',
        )
        for patron in patrones:
            coincidencia = re.search(patron, texto)
            if coincidencia:
                return coincidencia.group(1)
    except Exception as error:
        print(f"No se pudo resolver {handle}: {error}")

    return None


def resolver_handles_artistas(artistas):
    """
    Completa el channel_id de los artistas configurados con "handle".
    Si no se puede resolver, ese artista se omite en esta ejecución
    (sin alertas ni cambios en el estado).
    """
    resultado = []
    for artista in artistas:
        handle = artista.get("handle")
        if handle and not artista.get("channel_id"):
            channel_id = resolver_handle_a_channel_id(handle)
            if not channel_id:
                print(
                    f"AVISO: no se pudo resolver {handle} "
                    f"({artista.get('nombre')}); se omite en esta ejecución."
                )
                continue
            print(f"Resuelto {handle} -> {channel_id}")
            artista = {**artista, "channel_id": channel_id}
        resultado.append(artista)
    return resultado


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

    # Completa los channel_id de artistas configurados por @usuario.
    ARTISTAS[:] = resolver_handles_artistas(ARTISTAS)

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

    ids_monitorizados = ids_canales_monitorizados()
    albumes_colaboraciones = {}

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

        # Colaboraciones alojadas en el canal de otro artista.
        if BUSCAR_COLABORACIONES:
            canciones.extend(
                buscar_colaboraciones_artista(
                    ytmusic,
                    artista,
                    ids_monitorizados,
                    canciones_publicadas,
                    albumes_colaboraciones,
                )
            )

        # Lanzamientos nuevos detectados en Deezer.
        if BUSCAR_EN_DEEZER:
            canciones.extend(
                buscar_lanzamientos_deezer(
                    artista,
                    canciones_publicadas,
                )
            )

        # Registra la clave (artista + título) de las canciones ya
        # conocidas, para reconocerlas si reaparecen con otro ID.
        for cancion in canciones:
            if cancion.get("id") in canciones_publicadas:
                registrar_claves_cancion(canciones_publicadas, cancion)

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
            clave_base = clave_base_cancion(cancion)

            # Misma canción con otro ID o desde otra fuente
            if (
                clave in canciones_publicadas
                or clave_base in canciones_publicadas
                or clave in detectadas_en_esta_ejecucion
                or clave_base in detectadas_en_esta_ejecucion
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
                registrar_claves_cancion(canciones_publicadas, cancion)
                continue

            detectadas_en_esta_ejecucion.add(
                cancion_id
            )
            detectadas_en_esta_ejecucion.add(
                clave
            )
            detectadas_en_esta_ejecucion.add(
                clave_base
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

        # El preview se busca antes de publicar: si no hay preview,
        # el botón de YouTube Music va en el post principal.
        preview = None
        if ENVIAR_PREVIEW_AUDIO:
            preview = buscar_preview(cancion)

        exito, error = (
            publicar_cancion(
                ytmusic,
                cancion,
                con_boton=(BOTON_EN_POST or preview is None),
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
            registrar_claves_cancion(
                canciones_publicadas,
                cancion,
            )

            # Guardado inmediato.
            guardar_estado(
                estado
            )

            publicadas += 1

            # Adelanto de audio justo debajo de la publicación.
            # Orden garantizado: Post -> Audio -> siguiente Post -> Audio.
            # Todo se envía de forma secuencial, una canción a la vez.
            if preview:
                enviar_preview_audio(cancion, preview)

            time.sleep(PAUSA_ENTRE_PUBLICACIONES)

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
