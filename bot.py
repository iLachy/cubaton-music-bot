import os
import time
import requests
from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN DE TELEGRAM
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = "@Cubaton_Music"


# ============================================================
# ARTISTAS MONITORIZADOS
# ============================================================

ARTISTAS = [
    {
        "name": "Bebeshito",
        "channel_id": "UCpVfWS-cPOE2sYqsFuuP_Qg"
    },
    {
        "name": "Charly & Johayron",
        "channel_id": "UCnwEtOQyXJUUuBhcTgImdfQ"
    },
    {
        "name": "Dany Ome",
        "channel_id": "UCJQEm9t4KjDn-I8Fahf4Uqw"
    },
    {
        "name": "Wampi",
        "channel_id": "UCbfzw8u1lCwDMv443StJEOw"
    },
    {
        "name": "El Taiger",
        "channel_id": "UCoYtt7bGCV5RyUweyQgqQ4A"
    },
    {
        "name": "Ja Rulay",
        "channel_id": "UCcaU4COep7mj8kbXwS24JFQ"
    },
    {
        "name": "L Kimii",
        "channel_id": "UCMyQosiL8iVUtXPIm1UZJQg"
    },
    {
        "name": "El Dray",
        "channel_id": "UC4kpn8y8QXYXmyDn8HJKD8Q"
    },
    {
        "name": "Mauro y El Pitu",
        "channel_id": "UCvN1mRFfAfWYTiIkM70qUWA"
    },
    {
        "name": "Yirow Y El Tingo",
        "channel_id": "UCEq3_5h1Xi_vLbytP7OzuNA"
    },
    {
        "name": "Nany La Kbra",
        "channel_id": "UCG4lSNdNx_LuLnN2EW6uWwQ"
    },
    {
        "name": "Ya Ice Dilan",
        "channel_id": "UC9aJbR9Q8nscvZaMw_cH4Ww"
    },
    {
        "name": "Rey Tony",
        "channel_id": "UCDhExL0uVtumv_DEjPPq5qg"
    },
    {
        "name": "Baby Maikol",
        "channel_id": "UCP5R6Mgbk_bgtgzZguLNKdA"
    },
    {
        "name": "Payaso X Ley",
        "channel_id": "UCauTaqBvFqqqJTu3B4Wc1GA"
    },
    {
        "name": "Kaly Y Kowa",
        "channel_id": "UCSfR51myQhs2ZcdzrWo0Z4w"
    },
    {
        "name": "Wildey",
        "channel_id": "UCmFS-VSa4Wf3F1wdWS-8p_g"
    },
    {
        "name": "Wow Popy",
        "channel_id": "UCtFkN8UFxT_MuNdySlfuFuA"
    },
    {
        "name": "Talent Fuego",
        "channel_id": "UC0dVmcXfNa7lVeUBve3_FXw"
    },
    {
        "name": "Mawell",
        "channel_id": "UCL6P-jUDZEKBA-Lb6WFccWg"
    },
    {
        "name": "Harryson",
        "channel_id": "UC2ihX5uoblnN4wsA-ayIAAA"
    },
    {
        "name": "El Chulo",
        "channel_id": "UCiT8VNdnpeYnCTPJZoqym9g"
    },
    {
        "name": "Fixty Ordara",
        "channel_id": "UCDHDCbVOQywsLCsCZ8PH-AA"
    },
    {
        "name": "El Kamel",
        "channel_id": "UCPnWcazEV7QM0H7qBx6NVXg"
    },
    {
        "name": "Velito el Bufón",
        "channel_id": "UCRA9cRfAJXuxDRcFnoB7pwg"
    },
    {
        "name": "Un Titico",
        "channel_id": "UCT2KiGFSPZIF3DR9UIN2fYw"
    },
    {
        "name": "Musteerifa",
        "channel_id": "UCiT8PzlQqtPC7lWFh3--4jw"
    },
    {
        "name": "Chocolate MC",
        "channel_id": "UCYVuThmAmbXxk1o9Un5Cc_w"
    },
    {
        "name": "El Chacal",
        "channel_id": "UCJt4IsSmUjqTaamhCJoKK_g"
    },
    {
        "name": "El Micha",
        "channel_id": "UCHhrMSqe_C1E_JBEz3mRlew"
    },
    {
        "name": "Yomil",
        "channel_id": "UCPfXwOpwRIbVsqqTsgt4i5g"
    },
    {
        "name": "Jacob Forever",
        "channel_id": "UCJ1-Pwsroy-gzMqlfKDF4Hg"
    },
    {
        "name": "Gente de Zona",
        "channel_id": "UCl2KQVc_GFH081i7b9CJQug"
    },
    {
        "name": "La Diosa",
        "channel_id": "UChbVOQHgq01JoHY4axuWV0A"
    },
    {
        "name": "Seidy La Niña",
        "channel_id": "UCFqYfgj_7h3ZUkBnyYS-TFg"
    }
]


# ============================================================
# COMPROBAR TOKEN
# ============================================================

if not TELEGRAM_BOT_TOKEN:
    print("ERROR: No se encontró TELEGRAM_BOT_TOKEN.")
    raise SystemExit(1)


# ============================================================
# INICIALIZAR YOUTUBE MUSIC
# ============================================================

ytmusic = YTMusic()


# ============================================================
# FUNCIÓN PARA FORMATEAR ARTISTAS
# ============================================================

def formatear_artistas(artistas):

    nombres = []

    for artista in artistas:

        nombre = artista.get("name", "").strip()

        if not nombre:
            continue

        # Evitar duplicados
        if nombre.lower() not in [
            x.lower() for x in nombres
        ]:
            nombres.append(nombre)


    # --------------------------------------------------------
    # Si no hay artistas, usamos el artista monitorizado.
    # --------------------------------------------------------

    if not nombres:
        return None


    # --------------------------------------------------------
    # REGLA ESPECIAL:
    # Rey Tony + Helabusador
    # --------------------------------------------------------

    nombres_lower = [x.lower() for x in nombres]

    if (
        "rey tony" in nombres_lower
        and "helabusador" in nombres_lower
    ):

        nuevos = []

        for nombre in nombres:

            if nombre.lower() not in [
                "rey tony",
                "helabusador"
            ]:
                nuevos.append(nombre)

        nuevos.append("Rey Tony & Helabusador")

        nombres = nuevos


    # --------------------------------------------------------
    # REGLA ESPECIAL:
    # Dany Ome + Kevincito el 13
    # --------------------------------------------------------

    nombres_lower = [x.lower() for x in nombres]

    if (
        "dany ome" in nombres_lower
        and "kevincito el 13" in nombres_lower
    ):

        nuevos = []

        for nombre in nombres:

            if nombre.lower() not in [
                "dany ome",
                "kevincito el 13"
            ]:
                nuevos.append(nombre)

        nuevos.append("Dany Ome, Kevincito el 13")

        nombres = nuevos


    # --------------------------------------------------------
    # Separador:
    #
    # Siempre usamos coma entre artistas.
    #
    # Los dúos especiales ya fueron unidos arriba.
    # --------------------------------------------------------

    return ", ".join(nombres)


# ============================================================
# FUNCIÓN PARA OBTENER EL LANZAMIENTO MÁS RECIENTE
# ============================================================

def obtener_ultimo_lanzamiento(artista):

    nombre_monitorizado = artista["name"]
    channel_id = artista["channel_id"]


    print()
    print("=" * 60)
    print(f"CONSULTANDO: {nombre_monitorizado}")
    print("=" * 60)


    # --------------------------------------------------------
    # CONSULTAR ARTISTA
    # --------------------------------------------------------

    try:

        datos_artista = ytmusic.get_artist(channel_id)

    except Exception as e:

        print("ERROR CONSULTANDO ARTISTA:")
        print(e)

        return None


    # --------------------------------------------------------
    # RECOPILAR SINGLES Y ÁLBUMES
    # --------------------------------------------------------

    lanzamientos = []


    singles = datos_artista.get("singles", {})

    if isinstance(singles, dict):

        resultados = singles.get("results", [])

        if resultados:
            lanzamientos.extend(resultados)


    albums = datos_artista.get("albums", {})

    if isinstance(albums, dict):

        resultados = albums.get("results", [])

        if resultados:
            lanzamientos.extend(resultados)


    if not lanzamientos:

        print("No se encontraron lanzamientos.")

        return None


    # --------------------------------------------------------
    # PRIMER LANZAMIENTO = MÁS RECIENTE
    # --------------------------------------------------------

    lanzamiento = lanzamientos[0]


    titulo = lanzamiento.get("title", "Sin título")
    tipo = lanzamiento.get("type", "Release")
    anio = lanzamiento.get("year", "")

    browse_id = lanzamiento.get("browseId")


    # --------------------------------------------------------
    # PORTADA
    # --------------------------------------------------------

    thumbnails = lanzamiento.get("thumbnails", [])


    if not thumbnails:

        print("No se encontró portada.")

        return None


    portada = thumbnails[-1].get("url")


    if not portada:

        print("No se encontró URL de portada.")

        return None


    # --------------------------------------------------------
    # CONSULTAR DETALLE DEL LANZAMIENTO
    # --------------------------------------------------------

    artistas_detalle = []
    video_id = None


    if browse_id:

        try:

            detalle = ytmusic.get_album(browse_id)


            # ------------------------------------------------
            # ARTISTAS DEL LANZAMIENTO
            # ------------------------------------------------

            artistas_detalle = detalle.get("artists", [])


            # ------------------------------------------------
            # VIDEO ID
            # ------------------------------------------------

            tracks = detalle.get("tracks", [])


            if tracks:

                video_id = tracks[0].get("videoId")


        except Exception as e:

            print("ADVERTENCIA: No se pudo obtener el detalle.")
            print(e)


    # --------------------------------------------------------
    # FORMATEAR ARTISTAS
    # --------------------------------------------------------

    artistas_formateados = formatear_artistas(
        artistas_detalle
    )


    # Si no encontramos artistas en el detalle,
    # usamos el artista que estamos monitorizando.

    if not artistas_formateados:

        artistas_formateados = nombre_monitorizado


    # --------------------------------------------------------
    # URL DE YOUTUBE MUSIC
    # --------------------------------------------------------

    if video_id:

        url_youtube = (
            f"https://music.youtube.com/watch?v={video_id}"
        )

    else:

        consulta = (
            f"{artistas_formateados} {titulo}"
        )

        url_youtube = (
            "https://music.youtube.com/search?q="
            + requests.utils.quote(consulta)
        )


    # --------------------------------------------------------
    # MOSTRAR INFORMACIÓN
    # --------------------------------------------------------

    print()
    print("DATOS DEL LANZAMIENTO:")
    print(f"Artista(s): {artistas_formateados}")
    print(f"Título: {titulo}")
    print(f"Tipo: {tipo}")
    print(f"Año: {anio}")
    print(f"Video ID: {video_id}")


    return {
        "artistas": artistas_formateados,
        "titulo": titulo,
        "tipo": tipo,
        "anio": anio,
        "portada": portada,
        "url_youtube": url_youtube
    }


# ============================================================
# FUNCIÓN PARA PUBLICAR
# ============================================================

def publicar_lanzamiento(datos):

    # --------------------------------------------------------
    # TEXTO FINAL
    # --------------------------------------------------------

    texto = (
        f"🎤 <b>{datos['artistas']}</b>\n"
        f"<blockquote>🎵 <b>{datos['titulo']}</b></blockquote>\n"
        f"📀 <b>Tipo:</b> {datos['tipo']}\n"
        f"🗓 {datos['anio']}\n"
        f"\n"
        f"@Cubaton_Music"
    )


    # --------------------------------------------------------
    # BOTÓN
    # --------------------------------------------------------

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "▶️ Escuchar en YouTube Music",
                    "url": datos["url_youtube"]
                }
            ]
        ]
    }


    # --------------------------------------------------------
    # PAYLOAD
    # --------------------------------------------------------

    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "photo": datos["portada"],
        "caption": texto,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }


    telegram_url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendPhoto"
    )


    # --------------------------------------------------------
    # ENVIAR
    # --------------------------------------------------------

    try:

        respuesta = requests.post(
            telegram_url,
            json=payload,
            timeout=30
        )

    except Exception as e:

        print()
        print("ERROR DE CONEXIÓN CON TELEGRAM:")
        print(e)

        return False


    # --------------------------------------------------------
    # COMPROBAR RESULTADO
    # --------------------------------------------------------

    if respuesta.ok:

        resultado = respuesta.json()

        if resultado.get("ok"):

            print("PUBLICADO CORRECTAMENTE.")

            return True


    print()
    print("ERROR AL PUBLICAR:")
    print(respuesta.text)

    return False


# ============================================================
# PROCESO PRINCIPAL
# ============================================================

print()
print("=" * 60)
print("CUBATON MUSIC")
print("REPUBLICACIÓN DE LOS 35 LANZAMIENTOS")
print("VERSIÓN CON COLABORACIONES")
print("=" * 60)

print()
print(f"Total de artistas: {len(ARTISTAS)}")
print(f"Canal: {TELEGRAM_CHANNEL}")


publicados = 0
errores = 0


# ============================================================
# RECORRER ARTISTAS
# ============================================================

for numero, artista in enumerate(ARTISTAS, start=1):

    print()
    print()
    print("#" * 60)
    print(f"ARTISTA {numero}/{len(ARTISTAS)}")
    print("#" * 60)


    datos = obtener_ultimo_lanzamiento(artista)


    if not datos:

        errores += 1

        print()
        print(
            f"NO SE PUDO PROCESAR: "
            f"{artista['name']}"
        )

        continue


    resultado = publicar_lanzamiento(datos)


    if resultado:

        publicados += 1

    else:

        errores += 1


    # --------------------------------------------------------
    # PAUSA ENTRE PUBLICACIONES
    # --------------------------------------------------------

    if numero < len(ARTISTAS):

        print()
        print("Esperando 3 segundos...")
        time.sleep(3)


# ============================================================
# RESUMEN FINAL
# ============================================================

print()
print()
print("=" * 60)
print("PROCESO FINALIZADO")
print("=" * 60)

print()
print(f"Artistas procesados: {len(ARTISTAS)}")
print(f"Publicaciones exitosas: {publicados}")
print(f"Errores: {errores}")

print()


if errores == 0:

    print(
        "TODAS LAS 35 PUBLICACIONES "
        "FUERON ENVIADAS CORRECTAMENTE."
    )

else:

    print(
        "El proceso terminó, pero hubo "
        "artistas con errores."
    )


print()
print("=" * 60)
print("FIN")
print("=" * 60)
