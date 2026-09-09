import os
import json
from ytmusicapi import YTMusic

VIDEO_ID = "AU_l1Rn_nJI"
TITULO = "Pal Piso"
ARTISTAS = "LA R, Musteerifa, Vittorio Di Benedetto"


def imprimir_thumbnails(etiqueta, objeto):
    print()
    print("-" * 72)
    print(etiqueta)
    print("-" * 72)

    if not isinstance(objeto, dict):
        print("Objeto no válido.")
        return 0

    thumbnails = objeto.get("thumbnails") or []
    if not isinstance(thumbnails, list) or not thumbnails:
        print("No contiene thumbnails.")
        return 0

    total = 0
    for indice, thumb in enumerate(thumbnails, start=1):
        if not isinstance(thumb, dict):
            continue

        url = thumb.get("url", "")
        width = thumb.get("width", "?")
        height = thumb.get("height", "?")

        print(f"[{indice}] {width}x{height}")
        print(f"    {url}")
        total += 1

    print(f"Total de miniaturas: {total}")
    return total


def main():
    print("=" * 72)
    print("CUBATON MUSIC BOT - DIAGNÓSTICO DE PORTADA")
    print("=" * 72)
    print("⚠️ PRUEBA SOLO DE LECTURA")
    print("state/releases.json NO será leído ni modificado.")
    print("Telegram NO recibirá ninguna publicación.")
    print()
    print(f"Video ID: {VIDEO_ID}")
    print(f"Título: {TITULO}")
    print(f"Artistas: {ARTISTAS}")
    print("=" * 72)

    ytmusic = YTMusic()

    # 1. Video exacto: fuente principal.
    print()
    print("CONSULTANDO get_song() CON EL VIDEO ID EXACTO...")
    try:
        song = ytmusic.get_song(VIDEO_ID)
    except Exception as error:
        print(f"ERROR en get_song(): {error}")
        return

    print(f"Título devuelto: {song.get('title')}")
    print(f"Video ID devuelto: {song.get('videoId')}")
    print(f"Artistas devueltos: {', '.join(a.get('name', '') for a in (song.get('artists') or []) if isinstance(a, dict))}")
    imprimir_thumbnails("THUMBNAILS DEL get_song()", song)

    album = song.get("album")
    if isinstance(album, dict):
        print()
        print(f"Álbum asociado: {album.get('name') or album.get('title')}")
        print(f"Browse ID: {album.get('id') or album.get('browseId')}")
        imprimir_thumbnails("THUMBNAILS DEL ÁLBUM ASOCIADO", album)

    # 2. Búsqueda exacta para comparar qué portada entrega el resultado.
    consulta = f"{TITULO} {ARTISTAS}"
    print()
    print("CONSULTANDO search(filter='songs')...")
    print(f"Consulta: {consulta}")

    try:
        resultados = ytmusic.search(
            consulta,
            filter="songs",
            limit=10,
            ignore_spelling=True,
        )
    except Exception as error:
        print(f"ERROR en search(): {error}")
        resultados = []

    coincidentes = 0
    for indice, resultado in enumerate(resultados, start=1):
        if not isinstance(resultado, dict):
            continue

        titulo = str(resultado.get("title") or "").strip()
        video = resultado.get("videoId")
        artistas_resultado = ", ".join(
            a.get("name", "")
            for a in (resultado.get("artists") or [])
            if isinstance(a, dict)
        )

        print()
        print(f"RESULTADO DE BÚSQUEDA #{indice}")
        print(f"Título: {titulo}")
        print(f"Video ID: {video}")
        print(f"Artistas: {artistas_resultado}")

        if video == VIDEO_ID or titulo.casefold() == TITULO.casefold():
            coincidentes += 1
            imprimir_thumbnails(f"THUMBNAILS DEL RESULTADO #{indice}", resultado)
            resultado_album = resultado.get("album")
            if isinstance(resultado_album, dict):
                imprimir_thumbnails(f"THUMBNAILS DEL ÁLBUM DEL RESULTADO #{indice}", resultado_album)

            print()
            print("CAMPOS COMPLETOS DEL RESULTADO COINCIDENTE")
            print("-" * 72)
            for clave, valor in resultado.items():
                if clave == "thumbnails":
                    continue
                try:
                    valor_mostrable = json.dumps(valor, ensure_ascii=False, indent=2)
                except Exception:
                    valor_mostrable = repr(valor)
                print(f"\n[{clave}]\n{valor_mostrable}")

    print()
    print("=" * 72)
    print("RESUMEN DEL DIAGNÓSTICO")
    print(f"Resultados coincidentes inspeccionados: {coincidentes}")
    print("No se descargó ninguna imagen.")
    print("No se modificó ninguna imagen.")
    print("No se envió nada a Telegram.")
    print("state/releases.json NO FUE LEÍDO NI MODIFICADO.")
    print("=" * 72)


if __name__ == "__main__":
    main()
