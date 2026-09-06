from ytmusicapi import YTMusic

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


def extraer_referencia(url):
    """
    Extrae la referencia útil del enlace de YouTube Music.

    Ejemplos:
    https://music.youtube.com/@bebeshito
    -> @bebeshito

    https://music.youtube.com/channel/UCxxxx
    -> UCxxxx
    """

    if "/channel/" in url:
        return url.split("/channel/")[1].split("?")[0].strip()

    if "/@" in url:
        return "@" + url.split("/@")[1].split("?")[0].strip()

    return url


def buscar_por_handle(handle):
    """
    Busca un canal/artista utilizando el handle proporcionado.
    """

    resultados = ytmusic.search(
        handle,
        filter="artists",
        limit=5
    )

    return resultados


def verificar_artista(nombre, url):
    print()
    print("=" * 90)
    print(f"ARTISTA: {nombre}")
    print(f"ENLACE:  {url}")
    print("=" * 90)

    referencia = extraer_referencia(url)

    print(f"Referencia: {referencia}")
    print()

    # Si ya tenemos directamente el channelId,
    # no necesitamos buscarlo.
    if referencia.startswith("UC"):
        channel_id = referencia

        try:
            datos = ytmusic.get_artist(channel_id)

            print("RESULTADO DIRECTO")
            print("-" * 90)
            print(f"Nombre YouTube Music : {datos.get('name')}")
            print(f"Channel ID           : {channel_id}")
            print(f"Seguidores           : {datos.get('subscribers')}")

            print()
            print("ESTADO: CANAL ENCONTRADO")

            return {
                "artist": nombre,
                "youtube_name": datos.get("name"),
                "channel_id": channel_id,
                "url": url,
                "status": "OK",
            }

        except Exception as e:
            print("ESTADO: ERROR")
            print(f"Detalle: {e}")

            return {
                "artist": nombre,
                "youtube_name": None,
                "channel_id": channel_id,
                "url": url,
                "status": "ERROR",
            }

    # Para los enlaces @handle hacemos una búsqueda.
    try:
        resultados = buscar_por_handle(referencia)

        if not resultados:
            print("NO SE ENCONTRARON RESULTADOS")

            return {
                "artist": nombre,
                "youtube_name": None,
                "channel_id": None,
                "url": url,
                "status": "NO_ENCONTRADO",
            }

        print("RESULTADOS ENCONTRADOS:")
        print("-" * 90)

        for i, resultado in enumerate(resultados, start=1):
            print(
                f"{i}. "
                f"{resultado.get('artist')} "
                f"| ID: {resultado.get('browseId')}"
            )

        # Tomamos el primer resultado para la verificación inicial.
        primero = resultados[0]

        channel_id = primero.get("browseId")
        youtube_name = primero.get("artist")

        print()
        print(f"SELECCIONADO: {youtube_name}")
        print(f"CHANNEL ID:   {channel_id}")

        if channel_id:
            try:
                datos = ytmusic.get_artist(channel_id)

                print()
                print("DATOS DEL CANAL")
                print("-" * 90)
                print(f"Nombre YouTube Music : {datos.get('name')}")
                print(f"Channel ID           : {channel_id}")
                print(f"Seguidores           : {datos.get('subscribers')}")

                return {
                    "artist": nombre,
                    "youtube_name": datos.get("name"),
                    "channel_id": channel_id,
                    "url": url,
                    "status": "OK",
                }

            except Exception as e:
                print()
                print(f"No se pudo abrir el perfil: {e}")

        return {
            "artist": nombre,
            "youtube_name": youtube_name,
            "channel_id": channel_id,
            "url": url,
            "status": "REVISAR",
        }

    except Exception as e:
        print(f"ERROR: {e}")

        return {
            "artist": nombre,
            "youtube_name": None,
            "channel_id": None,
            "url": url,
            "status": "ERROR",
        }


print()
print("=" * 90)
print("VERIFICACIÓN DE LOS 38 ARTISTAS")
print("YOUTUBE MUSIC")
print("=" * 90)

print()
print(f"Total de artistas: {len(ARTISTS)}")
print()

resultados_finales = []

for nombre, url in ARTISTS.items():

    resultado = verificar_artista(nombre, url)

    resultados_finales.append(resultado)


print()
print()
print("=" * 90)
print("RESUMEN FINAL")
print("=" * 90)

for resultado in resultados_finales:

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
