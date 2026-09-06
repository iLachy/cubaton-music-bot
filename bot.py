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
# ARTISTAS
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
    print("ERROR: No se encontró el secreto TELEGRAM_BOT_TOKEN.")
    raise SystemExit(1)


# ============================================================
# INICIALIZAR YOUTUBE MUSIC
# ============================================================

ytmusic = YTMusic()


# ============================================================
# FUNCIÓN: OBTENER LANZAMIENTO MÁS RECIENTE
# ============================================================

def obtener_ultimo_lanzamiento(artista):

    nombre = artista["name"]
    channel_id = artista["channel_id"]

    print()
    print("=" * 60)
    print(f"CONSULTANDO: {nombre}")
    print("=" * 60)

    try:
        datos_artista = ytmusic.get_artist(channel_id)

    except Exception as e:

        print(f"ERROR consultando {nombre}:")
        print(e)

        return None


    lanzamientos = []

    singles = datos_artista.get("singles", {})
    albums = datos_artista.get("albums", {})


    if isinstance(singles, dict):
        resultados = singles.get("results", [])

        if resultados:
            lanzamientos.extend(resultados)


    if isinstance(albums, dict):
        resultados = albums.get("results", [])

        if resultados:
            lanzamientos.extend(resultados)


    if not lanzamientos:

        print("No se encontraron lanzamientos.")

        return None


    # --------------------------------------------------------
    # El primer resultado de la lista corresponde normalmente
    # al lanzamiento más reciente.
    # --------------------------------------------------------

    lanzamiento = lanzamientos[0]


    titulo = lanzamiento.get("title", "Sin título")
    tipo = lanzamiento.get("type", "Release")
    anio = lanzamiento.get("year", "")

    browse_id = lanzamiento.get("browseId")

    thumbnails = lanzamiento.get("thumbnails", [])


    if not thumbnails:

        print("No se encontró portada.")

        return None


    portada = thumbnails[-1].get("url")


    if not portada:

        print("La portada no contiene URL.")

        return None


    # --------------------------------------------------------
    # OBTENER VIDEO ID
    # --------------------------------------------------------

    video_id = None


    if browse_id:

        try:

            detalle = ytmusic.get_album(browse_id)

            tracks = detalle.get("tracks", [])


            if tracks:

                video_id = tracks[0].get("videoId")


        except Exception as e:

            print("Advertencia: no se pudo consultar el detalle.")
            print(e)


    # --------------------------------------------------------
    # CREAR URL DE YOUTUBE MUSIC
    # --------------------------------------------------------

    if video_id:

        url_youtube = (
            f"https://music.youtube.com/watch?v={video_id}"
        )

    else:

        consulta = f"{nombre} {titulo}"

        url_youtube = (
            "https://music.youtube.com/search?q="
            + requests.utils.quote(consulta)
        )


    # --------------------------------------------------------
    # MOSTRAR DATOS
    # --------------------------------------------------------

    print()
    print(f"Artista: {nombre}")
    print(f"Título: {titulo}")
    print(f"Tipo: {tipo}")
    print(f"Año: {anio}")
    print(f"Video ID: {video_id}")


    return {
        "artista": nombre,
        "titulo": titulo,
        "tipo": tipo,
        "anio": anio,
        "portada": portada,
        "url_youtube": url_youtube
    }


# ============================================================
# FUNCIÓN: PUBLICAR EN TELEGRAM
# ============================================================

def publicar_lanzamiento(datos):

    texto = (
        f"🎤 <b>{datos['artista']}</b>\n"
        f"<blockquote>🎵 <b>{datos['titulo']}</b></blockquote>\n"
        f"📀 <b>Tipo:</b> {datos['tipo']}\n"
        f"🗓 {datos['anio']}\n"
        f"\n"
        f"@Cubaton_Music"
    )


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


    if respuesta.ok:

        resultado = respuesta.json()

        if resultado.get("ok"):

            print()
            print("PUBLICADO CORRECTAMENTE.")

            return True


    print()
    print("ERROR AL PUBLICAR EN TELEGRAM:")
    print(respuesta.text)

    return False


# ============================================================
# PROCESO PRINCIPAL
# ============================================================

print()
print("=" * 60)
print("CUBATON MUSIC")
print("PUBLICACIÓN INICIAL DE 35 LANZAMIENTOS")
print("=" * 60)

print()
print(f"Artistas configurados: {len(ARTISTAS)}")
print(f"Canal: {TELEGRAM_CHANNEL}")


publicados = 0
errores = 0


# ============================================================
# RECORRER LOS 35 ARTISTAS
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
        print(f"NO SE PUBLICÓ: {artista['name']}")

        continue


    resultado = publicar_lanzamiento(datos)


    if resultado:

        publicados += 1

    else:

        errores += 1


    # --------------------------------------------------------
    # Pausa para evitar realizar las publicaciones demasiado
    # rápidamente.
    # --------------------------------------------------------

    if numero < len(ARTISTAS):

        print()
        print("Esperando 3 segundos antes del siguiente artista...")
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

    print("TODOS LOS LANZAMIENTOS FUERON PUBLICADOS CORRECTAMENTE.")

else:

    print("El proceso terminó, pero algunos artistas tuvieron errores.")

print()
print("=" * 60)
print("FIN")
print("=" * 60)
