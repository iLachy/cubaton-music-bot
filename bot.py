from ytmusicapi import YTMusic


# ============================================================
# DIAGNÓSTICO CONTROLADO DE "PAL PISO"
# ============================================================

TITULO_OBJETIVO = "Pal Piso"
VIDEO_ID_OBJETIVO = "AU_l1Rn_nJI"
ARTISTA_OBJETIVO = "Musteerifa"
CANAL_MUSTEERIFA_NUEVO = "UCUmbJ10w6Sljv-zIv0iQxNw"


# ============================================================
# UTILIDADES
# ============================================================

def normalizar(texto):
    return " ".join(str(texto or "").strip().split()).casefold()


def extraer_artistas(artistas):
    resultado = []

    if not isinstance(artistas, list):
        return resultado

    for artista in artistas:
        if not isinstance(artista, dict):
            continue

        nombre = artista.get("name")
        if nombre:
            resultado.append(str(nombre).strip())

    return resultado


def contiene_musteerifa(nombres):
    objetivo = normalizar(ARTISTA_OBJETIVO)
    return any(normalizar(nombre) == objetivo for nombre in nombres)


def imprimir_resultado(numero, resultado):
    titulo = resultadotitulo = str(resultado.get("title") or "")
    video_id = str(resultado.get("videoId") or "")
    artistas = extraer_artistas(resultado.get("artists"))
    album = resultado.get("album")

    print()
    print("-" * 70)
    print(f"RESULTADO #{numero}")
    print("-" * 70)
    print(f"Título:      {resultadotitulo}")
    print(f"Video ID:    {video_id}")
    print(f"Artistas:    {', '.join(artistas) if artistas else '(ninguno)'}")
    print(f"¿Musteerifa?: {'SÍ' if contiene_musteerifa(artistas) else 'NO'}")

    if isinstance(album, dict):
        print(f"Álbum:       {album.get('name') or album.get('title') or '(sin título)'}")
        print(f"Album ID:    {album.get('id') or album.get('browseId') or '(sin ID)'}")
    else:
        print("Álbum:       (sin información)")

    print(f"Año:         {resultado.get('year') or '(vacío/no disponible)'}")
    print(f"Tipo vídeo:  {resultado.get('videoType') or '(no disponible)'}")
    print(f"Duración:    {resultado.get('duration') or '(no disponible)'}")
    print(f"Disponible:  {resultado.get('isAvailable')}")


def inspeccionar_resultado_por_video(ytmusic, resultado):
    """Inspecciona el álbum asociado cuando existe."""

    album = resultado.get("album")
    if not isinstance(album, dict):
        return

    album_id = album.get("id") or album.get("browseId")
    if not album_id:
        return

    print()
    print("  >> INSPECCIÓN DEL ÁLBUM ASOCIADO")
    print(f"  Album ID: {album_id}")

    try:
        datos_album = ytmusic.get_album(album_id)
    except Exception as error:
        print(f"  ERROR get_album(): {error}")
        return

    if not datos_album:
        print("  get_album() no devolvió datos.")
        return

    print(f"  Título álbum: {datos_album.get('title') or '(vacío)'}")
    print(f"  Tipo álbum:   {datos_album.get('type') or '(vacío)'}")
    print(f"  Año álbum:    {datos_album.get('year') or '(vacío)'}")
    print(f"  Tracks:       {len(datos_album.get('tracks') or [])}")

    thumbnails = datos_album.get("thumbnails") or []
    print(f"  Thumbnails:   {len(thumbnails)}")

    if thumbnails:
        for indice, thumbnail in enumerate(thumbnails, start=1):
            if not isinstance(thumbnail, dict):
                continue
            print(
                f"    #{indice}: "
                f"{thumbnail.get('width')}x{thumbnail.get('height')} "
                f"{thumbnail.get('url', '')}"
            )

    tracks = datos_album.get("tracks") or []
    for track in tracks:
        if str(track.get("videoId") or "") == VIDEO_ID_OBJETIVO:
            print()
            print("  >> TRACK OBJETIVO EN EL ÁLBUM")
            print(f"  Título:   {track.get('title') or '(vacío)'}")
            print(f"  Video ID: {track.get('videoId') or '(vacío)'}")
            print(f"  Año:      {track.get('year') or '(vacío)'}")
            print(
                "  Artistas: "
                + ", ".join(extraer_artistas(track.get("artists")))
            )
            break


def buscar(ytmusic, consulta, limite=20):
    print()
    print("=" * 70)
    print(f"BUSCANDO: {consulta}")
    print("=" * 70)

    try:
        resultados = ytmusic.search(
            consulta,
            filter="songs",
            limit=limite,
            ignore_spelling=True,
        )
    except Exception as error:
        print(f"ERROR en search(): {error}")
        return []

    print(f"Resultados recibidos: {len(resultados)}")

    for indice, resultado in enumerate(resultados, start=1):
        imprimir_resultado(indice, resultado)

    return resultados


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("=" * 70)
    print("DIAGNÓSTICO DE PAL PISO")
    print("NO PUBLICA NADA")
    print("NO MODIFICA state/releases.json")
    print("=" * 70)
    print(f"Título objetivo:       {TITULO_OBJETIVO}")
    print(f"Video ID conocido:     {VIDEO_ID_OBJETIVO}")
    print(f"Artista objetivo:      {ARTISTA_OBJETIVO}")
    print(f"Canal nuevo Musteerifa:{CANAL_MUSTEERIFA_NUEVO}")

    ytmusic = YTMusic()

    consultas = [
        "Pal Piso",
        "Pal Piso Musteerifa",
        "Pal Piso LA R Musteerifa",
        "Pal Piso LA R Musteerifa Vittorio Di Benedetto",
    ]

    encontrados = []
    vistos_ids = set()

    for consulta in consultas:
        resultados = buscar(ytmusic, consulta, limite=20)

        for resultado in resultados:
            if not isinstance(resultado, dict):
                continue

            video_id = str(resultado.get("videoId") or "")
            if not video_id:
                continue

            if video_id in vistos_ids:
                continue

            vistos_ids.add(video_id)
            encontrados.append(resultado)

    print()
    print("=" * 70)
    print("ANÁLISIS DEL VIDEO ID CONOCIDO")
    print("=" * 70)

    coincidencia = None

    for resultado in encontrados:
        if str(resultado.get("videoId") or "") == VIDEO_ID_OBJETIVO:
            coincidencia = resultado
            break

    if coincidencia is None:
        print(
            "NO se encontró el video ID conocido "
            f"{VIDEO_ID_OBJETIVO} mediante ninguna de las búsquedas."
        )
    else:
        print(
            "SÍ se encontró automáticamente el video ID conocido: "
            f"{VIDEO_ID_OBJETIVO}"
        )
        imprimir_resultado(0, coincidencia)
        inspeccionar_resultado_por_video(ytmusic, coincidencia)

    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Resultados únicos analizados: {len(encontrados)}")
    print(
        "Video ID objetivo encontrado: "
        + ("SÍ" if coincidencia else "NO")
    )
    print("State modificado: NO")
    print("Telegram utilizado: NO")
    print("=" * 70)


if __name__ == "__main__":
    main()
