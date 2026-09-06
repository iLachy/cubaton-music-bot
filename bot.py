import os
import json
import html
import time
from datetime import datetime, timezone

import requests
from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@Cubaton_Music"

# Usuario/chat donde se recibirán las alertas de errores.
# Debes haber iniciado conversación con @CubatonMusicBot.
TELEGRAM_ALERT_CHAT_ID = "@CubatonMusicBot"

STATE_FILE = "state/releases.json"

ytmusic = YTMusic()


# ============================================================
# ARTISTAS MONITOREADOS
# ============================================================

ARTISTAS = {
    "Bebeshito": "UCpVfWS-cPOE2sYqsFuuP_Qg",
    "Charly & Johayron": "UCnwEtOQyXJUUuBhcTgImdfQ",
    "Dany Ome": "UCJQEm9t4KjDn-I8Fahf4Uqw",
    "Wampi": "UCbfzw8u1lCwDMv443StJEOw",
    "El Taiger": "UCoYtt7bGCV5RyUweyQgqQ4A",
    "Ja Rulay": "UCcaU4COep7mj8kbXwS24JFQ",
    "L Kimii": "UCMyQosiL8iVUtXPIm1UZJQg",
    "El Dray": "UC4kpn8y8QXYXmyDn8HJKD8Q",
    "Mauro y El Pitu": "UCvN1mRFfAfWYTiIkM70qUWA",
    "Yirow Y El Tingo": "UCEq3_5h1Xi_vLbytP7OzuNA",
    "Nany La Kbra": "UCG4lSNdNx_LuLnN2EW6uWwQ",
    "Ya Ice Dilan": "UC9aJbR9Q8nscvZaMw_cH4Ww",
    "Rey Tony": "UCDhExL0uVtumv_DEjPPq5qg",
    "Baby Maikol": "UCP5R6Mgbk_bgtgzZguLNKdA",
    "Payaso X Ley": "UCauTaqBvFqqqJTu3B4Wc1GA",
    "Kaly Y Kowa": "UCSfR51myQhs2ZcdzrWo0Z4w",
    "Wildey": "UCmFS-VSa4Wf3F1wdWS-8p_g",
    "Wow Popy": "UCtFkN8UFxT_MuNdySlfuFuA",
    "Talent Fuego": "UC0dVmcXfNa7lVeUBve3_FXw",
    "Mawell": "UCL6P-jUDZEKBA-Lb6WFccWg",
    "Harryson": "UC2ihX5uoblnN4wsA-ayIAAA",
    "El Chulo": "UCiT8VNdnpeYnCTPJZoqym9g",
    "Fixty Ordara": "UCDHDCbVOQywsLCsCZ8PH-AA",
    "El Kamel": "UCPnWcazEV7QM0H7qBx6NVXg",
    "Velito el Bufón": "UCRA9cRfAJXuxDRcFnoB7pwg",
    "Un Titico": "UCT2KiGFSPZIF3DR9UIN2fYw",
    "Musteerifa": "UCiT8PzlQqtPC7lWFh3--4jw",
    "Chocolate MC": "UCYVuThmAmbXxk1o9Un5Cc_w",
    "El Chacal": "UCJt4IsSmUjqTaamhCJoKK_g",
    "El Micha": "UCHhrMSqe_C1E_JBEz3mRlew",
    "Yomil": "UCPfXwOpwRIbVsqqTsgt4i5g",
    "Jacob Forever": "UCJ1-Pwsroy-gzMqlfKDF4Hg",
    "Gente de Zona": "UCl2KQVc_GFH081i7b9CJQug",
    "La Diosa": "UChbVOQHgq01JoHY4axuWV0A",
    "Seidy La Niña": "UCFqYfgj_7h3ZUkBnyYS-TFg",
}


# ============================================================
# ESTADO
# ============================================================

def cargar_estado():
    """
    Carga los lanzamientos ya conocidos.
    """

    if not os.path.exists(STATE_FILE):
        return {
            "version": 1,
            "releases": {}
        }

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:

            estado = json.load(archivo)

        if "releases" not in estado:
            estado["releases"] = {}

        return estado

    except Exception as e:

        print(f"ERROR leyendo estado: {e}")

        return {
            "version": 1,
            "releases": {}
        }


def guardar_estado(estado):
    """
    Guarda el estado de forma segura.
    """

    carpeta = os.path.dirname(STATE_FILE)

    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    archivo_temporal = STATE_FILE + ".tmp"

    with open(
        archivo_temporal,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            estado,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        archivo_temporal,
        STATE_FILE
    )


# ============================================================
# IDENTIFICACIÓN DE LANZAMIENTOS
# ============================================================

def obtener_id_lanzamiento(lanzamiento, canal_id):
    """
    Genera un identificador único.

    Prioridad:
    1. browseId
    2. videoId
    3. canal + título + año
    """

    browse_id = lanzamiento.get("browseId")

    if browse_id:
        return f"browse:{browse_id}"

    video_id = lanzamiento.get("videoId")

    if video_id:
        return f"video:{video_id}"

    titulo = (
        lanzamiento.get("title", "")
        .strip()
        .lower()
    )

    anio = str(
        lanzamiento.get("year", "")
    ).strip()

    return (
        f"fallback:{canal_id}:"
        f"{titulo}:{anio}"
    )


# ============================================================
# FORMATEAR ARTISTAS
# ============================================================

def formatear_artistas(artistas):
    """
    Formatea todos los artistas acreditados.

    Reglas especiales:

    Rey Tony + Helabusador
    -> Rey Tony & Helabusador

    Dany Ome + Kevincito el 13
    -> Dany Ome, Kevincito el 13
    """

    nombres = []

    for artista in artistas or []:

        nombre = artista.get(
            "name",
            ""
        ).strip()

        if not nombre:
            continue

        if not any(
            existente.lower() == nombre.lower()
            for existente in nombres
        ):

            nombres.append(nombre)

    nombres_lower = [
        nombre.lower()
        for nombre in nombres
    ]

    # --------------------------------------------------------
    # Rey Tony & Helabusador
    # --------------------------------------------------------

    if (
        "rey tony" in nombres_lower
        and
        "helabusador" in nombres_lower
    ):

        nombres = [
            nombre
            for nombre in nombres
            if nombre.lower()
            not in {
                "rey tony",
                "helabusador"
            }
        ]

        nombres.append(
            "Rey Tony & Helabusador"
        )

    # --------------------------------------------------------
    # Dany Ome, Kevincito el 13
    # --------------------------------------------------------

    if (
        "dany ome" in nombres_lower
        and
        "kevincito el 13" in nombres_lower
    ):

        nombres = [
            nombre
            for nombre in nombres
            if nombre.lower()
            not in {
                "dany ome",
                "kevincito el 13"
            }
        ]

        nombres.append(
            "Dany Ome, Kevincito el 13"
        )

    return ", ".join(nombres)


# ============================================================
# OBTENER DATOS COMPLETOS DEL LANZAMIENTO
# ============================================================

def obtener_datos_lanzamiento(
    lanzamiento,
    artista_principal
):
    """
    Obtiene la información necesaria para publicar.
    """

    titulo = lanzamiento.get(
        "title",
        "Sin título"
    )

    tipo = lanzamiento.get(
        "type",
        "Single"
    )

    anio = lanzamiento.get(
        "year",
        ""
    )

    browse_id = lanzamiento.get(
        "browseId"
    )

    thumbnail = None

    video_id = lanzamiento.get(
        "videoId"
    )

    artistas_creditados = []

    # --------------------------------------------------------
    # Thumbnail inicial
    # --------------------------------------------------------

    thumbnails = lanzamiento.get(
        "thumbnails",
        []
    )

    if thumbnails:

        thumbnail = thumbnails[-1].get(
            "url"
        )

    # --------------------------------------------------------
    # Obtener detalle desde YouTube Music
    # --------------------------------------------------------

    if browse_id:

        try:

            detalle = ytmusic.get_album(
                browse_id
            )

            artistas_creditados = (
                detalle.get(
                    "artists",
                    []
                )
            )

            # Fallback a los artistas del primer track
            if not artistas_creditados:

                tracks = detalle.get(
                    "tracks",
                    []
                )

                if tracks:

                    artistas_creditados = (
                        tracks[0].get(
                            "artists",
                            []
                        )
                    )

            # Thumbnail de mayor calidad
            detalle_thumbnails = (
                detalle.get(
                    "thumbnails",
                    []
                )
            )

            if detalle_thumbnails:

                thumbnail = (
                    detalle_thumbnails[-1]
                    .get("url")
                )

            # Video
            if not video_id:

                tracks = detalle.get(
                    "tracks",
                    []
                )

                if tracks:

                    video_id = (
                        tracks[0]
                        .get("videoId")
                    )

        except Exception as e:

            print(
                f"AVISO: No se pudo obtener "
                f"detalle de '{titulo}': {e}"
            )

    # --------------------------------------------------------
    # Fallback al artista monitoreado
    # --------------------------------------------------------

    if not artistas_creditados:

        artistas_creditados = [
            {
                "name": artista_principal
            }
        ]

    artistas_formateados = (
        formatear_artistas(
            artistas_creditados
        )
    )

    # --------------------------------------------------------
    # URL YouTube Music
    # --------------------------------------------------------

    if video_id:

        youtube_url = (
            "https://music.youtube.com/watch?v="
            f"{video_id}"
        )

    else:

        consulta = titulo.replace(
            " ",
            "+"
        )

        youtube_url = (
            "https://music.youtube.com/search?q="
            f"{consulta}"
        )

    # --------------------------------------------------------
    # ID único
    # --------------------------------------------------------

    release_id = (
        obtener_id_lanzamiento(
            lanzamiento,
            ARTISTAS[artista_principal]
        )
    )

    return {
        "id": release_id,
        "titulo": titulo,
        "tipo": tipo,
        "anio": anio,
        "artistas": artistas_formateados,
        "thumbnail": thumbnail,
        "youtube_url": youtube_url,
        "artista_detectado": artista_principal,
        "browse_id": browse_id,
        "video_id": video_id,
    }


# ============================================================
# OBTENER LANZAMIENTOS DEL ARTISTA
# ============================================================

def obtener_lanzamientos_artista(
    nombre,
    canal_id
):
    """
    Obtiene singles y álbumes actualmente visibles.
    """

    resultados = []

    try:

        artista = ytmusic.get_artist(
            canal_id
        )

        # ----------------------------------------------------
        # Singles
        # ----------------------------------------------------

        singles = artista.get(
            "singles",
            {}
        )

        if isinstance(
            singles,
            dict
        ):

            resultados.extend(
                singles.get(
                    "results",
                    []
                )
            )

        # ----------------------------------------------------
        # Álbumes
        # ----------------------------------------------------

        albums = artista.get(
            "albums",
            {}
        )

        if isinstance(
            albums,
            dict
        ):

            resultados.extend(
                albums.get(
                    "results",
                    []
                )
            )

        return resultados

    except Exception as e:

        print(
            f"ERROR obteniendo lanzamientos "
            f"de {nombre}: {e}"
        )

        return []


# ============================================================
# ENVIAR ALERTA PRIVADA
# ============================================================

def enviar_alerta_error(
    datos,
    error_detalle,
    etapa="Publicación"
):
    """
    Envía una alerta privada al propio bot
    cuando un lanzamiento no puede publicarse.
    """

    if not TELEGRAM_BOT_TOKEN:

        print(
            "No se puede enviar alerta: "
            "falta TELEGRAM_BOT_TOKEN."
        )

        return False

    artistas = html.escape(
        str(
            datos.get(
                "artistas",
                "Desconocido"
            )
        ),
        quote=False
    )

    titulo = html.escape(
        str(
            datos.get(
                "titulo",
                "Sin título"
            )
        ),
        quote=False
    )

    tipo = html.escape(
        str(
            datos.get(
                "tipo",
                "Desconocido"
            )
        ),
        quote=False
    )

    anio = html.escape(
        str(
            datos.get(
                "anio",
                ""
            )
        ),
        quote=False
    )

    error_texto = html.escape(
        str(error_detalle),
        quote=False
    )

    ahora = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    mensaje = (
        "🚨 <b>ERROR EN CUBATON MUSIC</b>\n"
        "\n"
        f"🎤 <b>Artista(s):</b> {artistas}\n"
        f"🎵 <b>Lanzamiento:</b> {titulo}\n"
        f"📀 <b>Tipo:</b> {tipo}\n"
        f"🗓 <b>Año:</b> {anio}\n"
        f"⚙️ <b>Etapa:</b> {html.escape(etapa)}\n"
        f"🕐 <b>Hora:</b> {ahora}\n"
        "\n"
        f"❌ <b>Error:</b>\n"
        f"<blockquote>{error_texto}</blockquote>\n"
        "\n"
        "ℹ️ El lanzamiento <b>NO</b> fue "
        "marcado como publicado y será "
        "intentado nuevamente en la próxima ejecución."
    )

    url = (
        "https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_ALERT_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }

    try:

        respuesta = requests.post(
            url,
            json=payload,
            timeout=30
        )

        if respuesta.ok:

            print(
                "ALERTA DE ERROR ENVIADA "
                "CORRECTAMENTE."
            )

            return True

        print(
            "NO SE PUDO ENVIAR LA ALERTA: "
            f"{respuesta.status_code} "
            f"{respuesta.text}"
        )

        return False

    except Exception as e:

        print(
            f"ERROR enviando alerta: {e}"
        )

        return False


# ============================================================
# PUBLICAR LANZAMIENTO
# ============================================================

def publicar_lanzamiento(datos):
    """
    Publica un lanzamiento.

    Devuelve:
        (True, None) si tuvo éxito
        (False, detalle_del_error) si falló
    """

    if not TELEGRAM_BOT_TOKEN:

        return (
            False,
            "TELEGRAM_BOT_TOKEN no está configurado."
        )

    if not datos.get("thumbnail"):

        return (
            False,
            "El lanzamiento no tiene portada "
            "(thumbnail) disponible."
        )

    artistas = html.escape(
        datos["artistas"],
        quote=False
    )

    titulo = html.escape(
        datos["titulo"],
        quote=False
    )

    tipo = html.escape(
        datos["tipo"],
        quote=False
    )

    anio = html.escape(
        str(datos["anio"]),
        quote=False
    )

    caption = (
        f"🎤 <b>{artistas}</b>\n"
        f"<blockquote>🎵 <b>{titulo}</b></blockquote>\n"
        f"📀 <b>Tipo:</b> {tipo}\n"
        f"🗓 {anio}\n"
        f"\n"
        f"@Cubaton_Music"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": (
                        "▶️ Escuchar en "
                        "YouTube Music"
                    ),
                    "url": datos["youtube_url"]
                }
            ]
        ]
    }

    url = (
        "https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendPhoto"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": datos["thumbnail"],
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }

    try:

        respuesta = requests.post(
            url,
            json=payload,
            timeout=30
        )

        if respuesta.ok:

            print(
                f"PUBLICADO: "
                f"{datos['artistas']} - "
                f"{datos['titulo']}"
            )

            return (
                True,
                None
            )

        detalle = (
            f"HTTP {respuesta.status_code}\n"
            f"Respuesta de Telegram:\n"
            f"{respuesta.text}"
        )

        print(
            f"ERROR TELEGRAM: {detalle}"
        )

        return (
            False,
            detalle
        )

    except Exception as e:

        detalle = (
            f"{type(e).__name__}: {str(e)}"
        )

        print(
            f"ERROR enviando a Telegram: "
            f"{detalle}"
        )

        return (
            False,
            detalle
        )


# ============================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================

def main():

    print("=" * 60)
    print("CUBATON MUSIC BOT")
    print("Detector automático de nuevos lanzamientos")
    print("=" * 60)

    if not TELEGRAM_BOT_TOKEN:

        print(
            "ERROR: No existe el secret "
            "TELEGRAM_BOT_TOKEN."
        )

        return

    estado = cargar_estado()

    releases_conocidos = estado[
        "releases"
    ]

    primera_ejecucion = (
        len(releases_conocidos) == 0
    )

    if primera_ejecucion:

        print()
        print(
            "PRIMERA EJECUCIÓN DETECTADA."
        )

        print(
            "Creando línea base."
        )

        print(
            "No se publicará ningún "
            "lanzamiento."
        )

        print()

    nuevos = []

    encontrados_ids = set()

    # ========================================================
    # RECORRER LOS 35 ARTISTAS
    # ========================================================

    for numero, (
        nombre,
        canal_id
    ) in enumerate(
        ARTISTAS.items(),
        start=1
    ):

        print(
            f"[{numero}/{len(ARTISTAS)}] "
            f"Comprobando: {nombre}"
        )

        lanzamientos = (
            obtener_lanzamientos_artista(
                nombre,
                canal_id
            )
        )

        for lanzamiento in lanzamientos:

            release_id = (
                obtener_id_lanzamiento(
                    lanzamiento,
                    canal_id
                )
            )

            # ------------------------------------------------
            # Evitar duplicados
            # ------------------------------------------------

            if release_id in encontrados_ids:
                continue

            encontrados_ids.add(
                release_id
            )

            # ------------------------------------------------
            # Ya conocido
            # ------------------------------------------------

            if release_id in releases_conocidos:
                continue

            # ------------------------------------------------
            # Obtener datos completos
            # ------------------------------------------------

            try:

                datos = (
                    obtener_datos_lanzamiento(
                        lanzamiento,
                        nombre
                    )
                )

            except Exception as e:

                print(
                    f"ERROR procesando "
                    f"lanzamiento: {e}"
                )

                datos = {
                    "id": release_id,
                    "titulo": lanzamiento.get(
                        "title",
                        "Sin título"
                    ),
                    "tipo": lanzamiento.get(
                        "type",
                        "Desconocido"
                    ),
                    "anio": lanzamiento.get(
                        "year",
                        ""
                    ),
                    "artistas": nombre,
                    "thumbnail": None,
                    "youtube_url": "",
                    "artista_detectado": nombre,
                    "browse_id": lanzamiento.get(
                        "browseId"
                    ),
                    "video_id": lanzamiento.get(
                        "videoId"
                    ),
                }

                if not primera_ejecucion:

                    enviar_alerta_error(
                        datos,
                        (
                            f"{type(e).__name__}: "
                            f"{str(e)}"
                        ),
                        etapa=(
                            "Obtención de "
                            "información"
                        )
                    )

                continue

            # ------------------------------------------------
            # Primera ejecución = línea base
            # ------------------------------------------------

            if primera_ejecucion:

                releases_conocidos[
                    release_id
                ] = {

                    "titulo": datos[
                        "titulo"
                    ],

                    "artistas": datos[
                        "artistas"
                    ],

                    "anio": datos[
                        "anio"
                    ],

                    "browse_id": datos[
                        "browse_id"
                    ],

                    "video_id": datos[
                        "video_id"
                    ],

                    "first_seen": datetime.now(
                        timezone.utc
                    ).isoformat()
                }

            else:

                nuevos.append(
                    datos
                )

        # Pausa entre artistas
        time.sleep(1)

    # ========================================================
    # PRIMERA EJECUCIÓN
    # ========================================================

    if primera_ejecucion:

        guardar_estado(
            estado
        )

        print()
        print("=" * 60)
        print(
            "LÍNEA BASE CREADA CORRECTAMENTE"
        )

        print(
            f"Lanzamientos registrados: "
            f"{len(releases_conocidos)}"
        )

        print(
            "No se publicó ningún "
            "lanzamiento."
        )

        print(
            "A partir de la próxima "
            "ejecución se detectarán "
            "las novedades."
        )

        print("=" * 60)

        return

    # ========================================================
    # PUBLICAR NUEVOS
    # ========================================================

    print()
    print(
        f"Nuevos lanzamientos detectados: "
        f"{len(nuevos)}"
    )

    publicados = 0
    errores = 0

    for datos in nuevos:

        print()
        print(
            f"Nuevo lanzamiento: "
            f"{datos['artistas']} - "
            f"{datos['titulo']}"
        )

        exito, error_detalle = (
            publicar_lanzamiento(
                datos
            )
        )

        if exito:

            # ----------------------------------------------
            # Solo se registra después de publicar
            # correctamente.
            # ----------------------------------------------

            releases_conocidos[
                datos["id"]
            ] = {

                "titulo": datos[
                    "titulo"
                ],

                "artistas": datos[
                    "artistas"
                ],

                "anio": datos[
                    "anio"
                ],

                "browse_id": datos[
                    "browse_id"
                ],

                "video_id": datos[
                    "video_id"
                ],

                "first_seen": datetime.now(
                    timezone.utc
                ).isoformat()
            }

            guardar_estado(
                estado
            )

            publicados += 1

        else:

            errores += 1

            print(
                "El lanzamiento NO será "
                "registrado como publicado."
            )

            # ----------------------------------------------
            # Enviar alerta privada
            # ----------------------------------------------

            enviar_alerta_error(
                datos,
                error_detalle,
                etapa="Publicación"
            )

        # Pausa entre publicaciones
        time.sleep(3)

    # ========================================================
    # GUARDAR ESTADO FINAL
    # ========================================================

    guardar_estado(
        estado
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)

    print(
        f"Lanzamientos nuevos detectados: "
        f"{len(nuevos)}"
    )

    print(
        f"Publicaciones exitosas: "
        f"{publicados}"
    )

    print(
        f"Errores: "
        f"{errores}"
    )

    print(
        f"Lanzamientos almacenados en estado: "
        f"{len(releases_conocidos)}"
    )

    print("=" * 60)

    if not nuevos:

        print(
            "NO HAY NUEVOS LANZAMIENTOS."
        )

    elif errores == 0:

        print(
            "TODOS LOS NUEVOS LANZAMIENTOS "
            "FUERON PUBLICADOS CORRECTAMENTE."
        )

    else:

        print(
            "ALGUNOS LANZAMIENTOS NO "
            "PUDIERON PUBLICARSE."
        )

        print(
            "Se enviaron alertas privadas "
            "con los errores detectados."
        )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()
