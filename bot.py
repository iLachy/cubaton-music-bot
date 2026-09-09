import os
import json
import html
import unicodedata
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
    """Obtiene el año de un track del fallback cuando no viene incluido."""

    anio_directo = track.get("year")
    if anio_directo:
        return anio_directo

    album = track.get("album")
    if isinstance(album, dict):
        album_id = album.get("id") or album.get("browseId")
        if album_id:
            try:
                datos_album = ytmusic.get_album(album_id)
                if datos_album and datos_album.get("year"):
                    return datos_album.get("year")
            except Exception:
                pass

    consultas = []
    nombres = [str(a).strip() for a in artistas if a]
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
                limit=10,
                ignore_spelling=True,
            )
        except Exception:
            continue

        for resultado in resultados:
            if str(resultado.get("title", "")).casefold() != str(titulo).casefold():
                continue

            artistas_resultado = extraer_artistas_de_objetos(
                resultado.get("artists")
            )

            if nombres and artistas_resultado:
                claves_busqueda = {normalizar_nombre(x) for x in nombres}
                claves_resultado = {normalizar_nombre(x) for x in artistas_resultado}
                if not (claves_busqueda & claves_resultado):
                    continue

            album_resultado = resultado.get("album")
            album_id = None
            if isinstance(album_resultado, dict):
                album_id = album_resultado.get("id") or album_resultado.get("browseId")

            if album_id:
                try:
                    datos_album = ytmusic.get_album(album_id)
                    if datos_album and datos_album.get("year"):
                        return datos_album.get("year")
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

                    cancion = crear_cancion_desde_track(
                        {
                            "videoId": video_id,
                            "title": titulo,
                            "artists": [
                                {"name": artista_nombre}
                                for artista_nombre in artistas
                            ],
                        },
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

def publicar_cancion(
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
    # MINIATURA
    # ========================================================

    video_id = cancion[
        "video_id"
    ]

    thumbnail_url = (
        "https://i.ytimg.com/vi/"
        f"{video_id}/hqdefault.jpg"
    )

    # ========================================================
    # DESCARGAR Y RECORTAR MINIATURA A CUADRADO
    # ========================================================

    try:
        imagen_respuesta = requests.get(
            thumbnail_url,
            timeout=30,
        )
        imagen_respuesta.raise_for_status()

        imagen = Image.open(
            BytesIO(imagen_respuesta.content)
        ).convert("RGB")

        imagen_cuadrada = ImageOps.fit(
            imagen,
            (800, 800),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

        buffer = BytesIO()
        imagen_cuadrada.save(
            buffer,
            format="JPEG",
            quality=95,
            optimize=True,
        )
        buffer.seek(0)

    except Exception as error:
        return (
            False,
            f"No se pudo preparar la portada cuadrada: {error}"
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

        return

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

            detectadas_en_esta_ejecucion.add(
                cancion_id
            )

            nuevas_canciones.append(
                cancion
            )

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

            # Guardado inmediato.
            guardar_estado(
                estado
            )

            publicadas += 1

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


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":
    main()
