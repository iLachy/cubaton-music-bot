from ytmusicapi import YTMusic
import requests
import re
import html


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
}


def normalizar(texto):
    """
    Normaliza texto para poder comparar nombres.
    """

    if not texto:
        return ""

    texto = html.unescape(texto)
    texto = texto.lower().strip()

    reemplazos = {
        "&": "and",
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
    }

    for viejo, nuevo in reemplazos.items():
        texto = texto.replace(viejo, nuevo)

    texto = re.sub(r"[^a-z0-9]+", " ", texto)

    return " ".join(texto.split())


def nombres_compatibles(esperado, obtenido):
    """
    Comprueba si el nombre de YouTube Music es razonablemente
    compatible con el nombre que nosotros esperamos.

    No intenta ser demasiado permisivo.
    """

    a = normalizar(esperado)
    b = normalizar(obtenido)

    if not a or not b:
        return False

    if a == b:
        return True

    palabras_a = set(a.split())
    palabras_b = set(b.split())

    # Coincidencia exacta de todas las palabras importantes.
    if palabras_a and palabras_a.issubset(palabras_b):
        return True

    if palabras_b and palabras_b.issubset(palabras_a):
        return True

    return False


def obtener_channel_id_desde_channel_url(url):
    """
    Si la URL ya contiene /channel/UC..., devuelve directamente
    ese Channel ID.
    """

    match = re.search(
        r"/channel/(UC[a-zA-Z0-9_-]{22})",
        url
    )

    if match:
        return match.group(1)

    return None


def obtener_handle(url):
    """
    Extrae el @handle de una URL.
    """

    match = re.search(
        r"/@([^/?]+)",
        url
    )

    if match:
        return match.group(1)

    return None


def obtener_html_canal(handle):
    """
    Descarga la página pública del canal y busca referencias
    al Channel ID.

    Probamos YouTube Music y YouTube normal.
    """

    urls = [
        f"https://music.youtube.com/@{handle}",
        f"https://www.youtube.com/@{handle}",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    for url in urls:

        print(f"Consultando: {url}")

        try:

            respuesta = requests.get(
                url,
                headers=headers,
                timeout=20,
                allow_redirects=True,
            )

            print(f"HTTP: {respuesta.status_code}")
            print(f"URL final: {respuesta.url}")

            if respuesta.status_code != 200:
                continue

            return respuesta.text

        except Exception as error:

            print(f"Error: {error}")

    return None


def extraer_channel_ids(texto):
    """
    Busca todos los Channel IDs que aparezcan en el HTML.
    """

    if not texto:
        return []

    patrones = [
        r'"channelId":"(UC[a-zA-Z0-9_-]{22})"',
        r'"externalId":"(UC[a-zA-Z0-9_-]{22})"',
        r'channelId\\":\\"(UC[a-zA-Z0-9_-]{22})',
        r'channelId%22%3A%22(UC[a-zA-Z0-9_-]{22})',
    ]

    encontrados = []

    for patron in patrones:

        matches = re.findall(patron, texto)

        for channel_id in matches:

            if channel_id not in encontrados:
                encontrados.append(channel_id)

    return encontrados


def comprobar_channel_id(
    nombre_esperado,
    channel_id,
    fuente,
):
    """
    Comprueba un Channel ID mediante ytmusicapi.
    """

    print()
    print(f"Comprobando ID: {channel_id}")
    print(f"Fuente: {fuente}")

    try:

        datos = ytmusic.get_artist(channel_id)

        nombre_youtube = datos.get("name")
        seguidores = datos.get("subscribers")

        print(f"Nombre devuelto: {nombre_youtube}")
        print(f"Seguidores: {seguidores}")

        compatible = nombres_compatibles(
            nombre_esperado,
            nombre_youtube
        )

        if compatible:

            print("RESULTADO: OK")

            return {
                "channel_id": channel_id,
                "youtube_name": nombre_youtube,
                "subscribers": seguidores,
                "status": "OK",
            }

        print("RESULTADO: REVISAR")
        print(
            f"El nombre esperado es '{nombre_esperado}', "
            f"pero YouTube Music devuelve '{nombre_youtube}'."
        )

        return {
            "channel_id": channel_id,
            "youtube_name": nombre_youtube,
            "subscribers": seguidores,
            "status": "REVISAR",
        }

    except Exception as error:

        print(f"ERROR YTMUSICAPI: {error}")

        return {
            "channel_id": channel_id,
            "youtube_name": None,
            "subscribers": None,
            "status": "ERROR",
        }


def verificar_artista(nombre, url):

    print()
    print("=" * 90)
    print(f"ARTISTA: {nombre}")
    print(f"URL:     {url}")
    print("=" * 90)

    # ---------------------------------------------------------
    # CASO 1
    # La URL ya tiene Channel ID.
    # ---------------------------------------------------------

    channel_id = obtener_channel_id_desde_channel_url(url)

    if channel_id:

        print()
        print("La URL contiene directamente un Channel ID.")

        resultado = comprobar_channel_id(
            nombre,
            channel_id,
            "URL /channel/"
        )

        return resultado


    # ---------------------------------------------------------
    # CASO 2
    # La URL utiliza @handle.
    # ---------------------------------------------------------

    handle = obtener_handle(url)

    if not handle:

        print("No se pudo extraer el handle.")

        return {
            "channel_id": None,
            "youtube_name": None,
            "subscribers": None,
            "status": "NO_ENCONTRADO",
        }


    print()
    print(f"Handle: @{handle}")

    texto = obtener_html_canal(handle)

    if not texto:

        print("No se pudo descargar la página.")

        return {
            "channel_id": None,
            "youtube_name": None,
            "subscribers": None,
            "status": "NO_ENCONTRADO",
        }


    channel_ids = extraer_channel_ids(texto)

    print()
    print(f"Channel IDs encontrados: {len(channel_ids)}")

    if not channel_ids:

        print("No se encontró ningún Channel ID.")

        return {
            "channel_id": None,
            "youtube_name": None,
            "subscribers": None,
            "status": "NO_ENCONTRADO",
        }


    # ---------------------------------------------------------
    # Comprobamos cada ID.
    # NUNCA elegimos simplemente el primero.
    # ---------------------------------------------------------

    resultados = []

    for candidato in channel_ids:

        resultado = comprobar_channel_id(
            nombre,
            candidato,
            f"@{handle}"
        )

        resultados.append(resultado)


    # ---------------------------------------------------------
    # Buscar coincidencia exacta.
    # ---------------------------------------------------------

    validos = [
        resultado
        for resultado in resultados
        if resultado["status"] == "OK"
    ]


    if len(validos) == 1:

        print()
        print("CANAL VALIDADO CORRECTAMENTE.")

        return validos[0]


    if len(validos) > 1:

        print()
        print("HAY VARIOS CANDIDATOS VÁLIDOS.")
        print("ESTADO: REVISAR")

        return {
            "channel_id": None,
            "youtube_name": None,
            "subscribers": None,
            "status": "REVISAR",
        }


    print()
    print("No se encontró coincidencia segura.")

    # Mostramos el primer candidato únicamente como
    # información, pero NO lo consideramos válido.

    if resultados:

        primero = resultados[0]

        return {
            "channel_id": primero.get("channel_id"),
            "youtube_name": primero.get("youtube_name"),
            "subscribers": primero.get("subscribers"),
            "status": "REVISAR",
        }

    return {
        "channel_id": None,
        "youtube_name": None,
        "subscribers": None,
        "status": "NO_ENCONTRADO",
    }


print()
print("=" * 90)
print("PASO 17")
print("VERIFICACIÓN ESTRICTA DE LOS 37 ARTISTAS")
print("=" * 90)

print()
print(f"Total de artistas: {len(ARTISTS)}")

resultados_finales = []


for nombre, url in ARTISTS.items():

    try:

        resultado = verificar_artista(
            nombre,
            url
        )

        resultados_finales.append({
            "artist": nombre,
            "url": url,
            **resultado,
        })

    except Exception as error:

        print()
        print("=" * 90)
        print(f"ERROR GENERAL: {nombre}")
        print(f"Detalle: {error}")
        print("=" * 90)

        resultados_finales.append({
            "artist": nombre,
            "url": url,
            "channel_id": None,
            "youtube_name": None,
            "subscribers": None,
            "status": "ERROR",
        })


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
print("TOTALES")
print("=" * 90)

ok = sum(
    1
    for r in resultados_finales
    if r["status"] == "OK"
)

revisar = sum(
    1
    for r in resultados_finales
    if r["status"] == "REVISAR"
)

no_encontrado = sum(
    1
    for r in resultados_finales
    if r["status"] == "NO_ENCONTRADO"
)

errores = sum(
    1
    for r in resultados_finales
    if r["status"] == "ERROR"
)

print(f"OK:             {ok}")
print(f"REVISAR:        {revisar}")
print(f"NO ENCONTRADO:  {no_encontrado}")
print(f"ERROR:          {errores}")

print()
print("=" * 90)
print("PASO 17 TERMINADO")
print("=" * 90)
