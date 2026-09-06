from ytmusicapi import YTMusic

ytmusic = YTMusic()


CANDIDATES = {
    "Wampi": [
        "UCbfzw8u1lCwDMv443StJEOw",
        "UC6mGHuUjSC78InOHqpWTIlg",
    ],

    "El Dray": [
        "UC4kpn8y8QXYXmyDn8HJKD8Q",
        "UCEhuYVGDegmiDPnclL3VALg",
    ],

    "Ya Ice Dilan": [
        "UC9aJbR9Q8nscvZaMw_cH4Ww",
        "UC2LV8lBrk6XhGXWEW6FQ5Yw",
    ],

    "Rey Tony": [
        "UCDhExL0uVtumv_DEjPPq5qg",
        "UC44Wl903rZyECDgd31QY0jw",
        "UCTCNLKtFIKj3ccASX-CxAQQ",
    ],

    "El Chulo": [
        "UCiT8VNdnpeYnCTPJZoqym9g",
        "UC1SO6N8zhEFpkeZ8RwB4-aQ",
        "UCFpUBfhecvSQ1b-Wfjep6SQ",
        "UCkR0TzTgWPXxzyYouqjcAfA",
    ],

    "Chocolate MC": [
        "UCYVuThmAmbXxk1o9Un5Cc_w",
        "UCKv7qrXw4z27Kil_UU8RPkA",
    ],

    "Yomil": [
        "UCPfXwOpwRIbVsqqTsgt4i5g",
        "UC3V7uL_r1yOl1Eagu08iQoA",
    ],

    "El Micha": [
        "UCHhrMSqe_C1E_JBEz3mRlew",
        "UCshkJg40zQSYMQfEU2sPRHw",
    ],

    "Divan": [
        "UClkrdbqStBnXkfm6JvcvLsA",
        "UCVOhy-LAg5JU2gXlSMnfuhg",
        "UCik9RxN7JDwObrXSalYHJIA",
    ],

    "Musteerifa": [
        "UCUmbJ10w6Sljv-zIv0iQxNw",
        "UCiT8PzlQqtPC7lWFh3--4jw",
        "UCL2y69awsxlPljbUNQTbHTg",
    ],

    "DJ Honda": [
        "UC7thYxXkCYkqZm_hQzny9aw",
        "UCVQLsyjNCa-GwEkshLN1Dfg",
    ],
}


def mostrar_artista(nombre, channel_id):

    print()
    print("=" * 80)
    print(f"ARTISTA: {nombre}")
    print(f"ID: {channel_id}")
    print("=" * 80)

    try:
        datos = ytmusic.get_artist(channel_id)

        print(f"Nombre YouTube Music: {datos.get('name')}")
        print(f"Descripción: {datos.get('description')}")
        print(f"Seguidores: {datos.get('subscribers')}")

        print()
        print("LANZAMIENTOS:")

        albums = datos.get("albums", {})

        resultados = albums.get("results", [])

        if not resultados:
            print("No aparecen lanzamientos en esta consulta.")
        else:
            for i, album in enumerate(resultados[:10], start=1):
                print(
                    f"{i}. {album.get('title')} "
                    f"| {album.get('type')} "
                    f"| {album.get('year')}"
                )

    except Exception as e:
        print(f"ERROR: {e}")


print("=" * 80)
print("VERIFICACIÓN DE CANALES DE ARTISTAS")
print("=" * 80)

for nombre, ids in CANDIDATES.items():

    for channel_id in ids:
        mostrar_artista(nombre, channel_id)


print()
print("=" * 80)
print("VERIFICACIÓN TERMINADA")
print("=" * 80)
