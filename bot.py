from ytmusicapi import YTMusic
import requests
import re

ytmusic = YTMusic()

ARTISTS = {
    "Bebeshito": "https://music.youtube.com/@bebeshito",
    "Charly & Johayron": "https://music.youtube.com/@charlyjohayron",
    "Dany Ome": "https://music.youtube.com/@danyome",
    "Kevincito El 13": "https://music.youtube.com/@kevincitoel13",
    "Wampi": "https://music.youtube.com/@wampi",
    "El Taiger": "https://music.youtube.com/@eltaiger",
    "Ja Rulay": "https://music.youtube.com/@jarulay",
    "L Kimii": "https://music.youtube.com/@lkimii9923",
    "El Dray": "https://music.youtube.com/@eseldray",
    "Mauro y El Pitu": "https://music.youtube.com/@mauropitu_",
    "Yirow Y El Tingo": "https://music.youtube.com/@elyirowyeltingo",
    "Nany La Kbra": "https://music.youtube.com/channel/UCG4lSNdNx_LuLnN2EW6uWwQ",
    "Ya Ice Dilan": "https://music.youtube.com/channel/UC9aJbR9Q8nscvZaMw_cH4Ww",
    "Rey Tony": "https://music.youtube.com/channel/UCDhExL0uVtumv_DEjPPq5qg",
    "Baby Maikol": "https://music.youtube.com/@babyymaikol",
    "Payaso X Ley": "https://music.youtube.com/@payasoxley",
    "Kaly Y Kowa": "https://music.youtube.com/@kalyykowa",
    "Wildey": "https://music.youtube.com/@wildeylucho",
    "Wow Popy": "https://music.youtube.com/@wowpopyoficiall",
    "Talent Fuego": "https://music.youtube.com/@talentfuego",
    "Mawell": "https://music.youtube.com/@mawelloficial",
    "Harryson": "https://music.youtube.com/@harryson1pesao",
    "El Chulo": "https://music.youtube.com/@elchulopa",
    "Fixty Ordara": "https://music.youtube.com/channel/UCDHDCbVOQywsLCsCZ8PH-AA",
    "El Kamel": "https://music.youtube.com/@elkameloficial",
    "Velito el Bufón": "https://music.youtube.com/@velitoelbufon",
    "Helabusador": "https://music.youtube.com/channel/UC89ct8d1ZKEXS03nSpntgPg",
    "Un Titico": "https://music.youtube.com/@untitico",
    "Musteerifa": "https://music.youtube.com/channel/UCiT8PzlQqtPC7lWFh3--4jw",
    "Chocolate MC": "https://music.youtube.com/@chocolatemcoficialyoutube",
    "El Chacal": "https://music.youtube.com/@chacalrlm",
    "El Micha": "https://music.youtube.com/@elmichaoficial1",
    "Yomil": "https://music.youtube.com/@yomil_champions",
    "Jacob Forever": "https://music.youtube.com/@jacobforeveroficial",
    "Gente de Zona": "https://music.youtube.com/@gentedezonaoficial",
    "La Diosa": "https://music.youtube.com/@ladiosa",
    "Seidy La Niña": "https://music.youtube.com/@seidylanina",
    "Divan": "https://music.youtube.com/@divanoficial",
}


def obtener_channel_id_desde_url(url):
    """
    Obtiene el channelId directamente desde un enlace de YouTube/YouTube Music.

    Si el enlace ya contiene /channel/UC..., devuelve ese ID.

    Si contiene un @handle, consulta la página pública de YouTube
    y busca el identificador del canal.
    """

    # ---------------------------------------------------------
    # CASO 1: URL que ya contiene channel/UC...
    # ---------------------------------------------------------

    if "/channel/" in url:

        channel_id = url.split("/channel/")[1].split("?")[0].strip()

        return channel_id


    # ---------------------------------------------------------
    # CASO 2: URL con @handle
    # ---------------------------------------------------------

    match = re.search(r"/@([^/?]+)", url)

    if not match:
        return None


    handle = match.group(1)

    print(f"Handle detectado: @{handle}")

    # Intentamos primero YouTube Music.
    urls = [
        f"https://music.youtube.com/@{handle}",
        f"https://www.youtube.com/@{handle}",
    ]


    for pagina in urls:

        try:

            print(f"Consultando: {pagina}")

            respuesta = requests.get(
                pagina,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/131.0 Safari/537.36"
                    )
                },
                timeout=20
            )

            print(f"HTTP: {respuesta.status_code}")

            if respuesta.status_code != 200:
                continue


            texto = respuesta.text


            # Buscamos el channelId dentro del HTML.
            patrones = [

                r'"channelId":"(UC[a-zA-Z0-9_-]{22})"',

                r'"externalId":"(UC[a-zA-Z0-9_-]{22})"',

                r'channelId\\":\\"(UC[a-zA-Z0-9_-]{22})',

            ]


            for patron in patrones:

                encontrado = re.search(patron, texto)

                if encontrado:

                    return encontrado.group(1)


        except Exception as e:

            print(f"Error consultando página: {e}")


    return None


def verificar_artista(nombre, url):

    print()
    print("=" * 90)
    print(f"ARTISTA: {nombre}")
    print(f"URL:     {url}")
    print("=" * 90)

    channel_id = obtener_channel_id_desde_url(url)


    if not channel_id:

        print()
        print("❌ NO SE PUDO OBTENER EL CHANNEL ID")

        return {
            "artist": nombre,
            "url": url,
            "channel_id": None,
            "youtube_name": None,
            "status": "NO_ENCONTRADO",
        }


    print()
    print(f"Channel ID encontrado: {channel_id}")


    try:

        datos = ytmusic.get_artist(channel_id)

        nombre_youtube = datos.get("name")

        seguidores = datos.get("subscribers")


        print()
        print("DATOS DE YOUTUBE MUSIC")
        print("-" * 90)

        print(f"Nombre:      {nombre_youtube}")
        print(f"Channel ID:  {channel_id}")
        print(f"Seguidores:  {seguidores}")

        print()
        print("✅ CANAL ENCONTRADO")


        return {
            "artist": nombre,
            "url": url,
            "channel_id": channel_id,
            "youtube_name": nombre_youtube,
            "status": "OK",
        }


    except Exception as e:

        print()
        print("⚠️ CHANNEL ID ENCONTRADO, PERO YTMUSICAPI NO PUDO ABRIRLO")
        print(f"Error: {e}")

        return {
            "artist": nombre,
            "url": url,
            "channel_id": channel_id,
            "youtube_name": None,
            "status": "ID_ENCONTRADO",
        }


print()
print("=" * 90)
print("PASO 16")
print("RESOLUCIÓN DIRECTA DE LOS 38 CANALES")
print("=" * 90)

print()
print(f"Total de artistas: {len(ARTISTS)}")


resultados = []


for nombre, url in ARTISTS.items():

    try:

        resultado = verificar_artista(nombre, url)

        resultados.append(resultado)

    except Exception as e:

        print()
        print("=" * 90)
        print(f"ERROR GENERAL: {nombre}")
        print(f"Detalle: {e}")
        print("=" * 90)

        resultados.append({
            "artist": nombre,
            "url": url,
            "channel_id": None,
            "youtube_name": None,
            "status": "ERROR",
        })


print()
print()
print("=" * 90)
print("RESUMEN FINAL")
print("=" * 90)

for resultado in resultados:

    print(
        f"{resultado['artist']} "
        f"-> "
        f"{resultado.get('youtube_name')} "
        f"-> "
        f"{resultado.get('channel_id')} "
        f"-> "
        f"{resultado.get('status')}"
    )


print()
print("=" * 90)
print("VERIFICACIÓN TERMINADA")
print("=" * 90)
