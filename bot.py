from ytmusicapi import YTMusic
import json

ALBUM_ID = "MPREb_2vLxqqdb9hf"
VIDEO_ID = "AU_l1Rn_nJI"

print("=" * 72)
print("PRUEBA SOLO DE LECTURA — ALBUM DE PAL PISO")
print("=" * 72)
print("state/releases.json NO será leído ni modificado.")
print("No se descargan imágenes, no se envía Telegram y no se modifica ningún archivo.")
print()

try:
    ytmusic = YTMusic()
except Exception as e:
    print(f"ERROR inicializando YTMusic: {e}")
    raise SystemExit(1)


def print_thumbnails(label, thumbnails):
    print(f"\n{label}")
    if not thumbnails:
        print("  No contiene thumbnails.")
        return

    for i, thumb in enumerate(thumbnails, 1):
        width = thumb.get("width", "?")
        height = thumb.get("height", "?")
        url = thumb.get("url", "")
        print(f"  [{i}] {width}x{height}")
        print(f"      {url}")


def print_album_summary(prefix, album):
    if not isinstance(album, dict):
        print(f"{prefix}: {album!r}")
        return

    print(f"{prefix}")
    for key in [
        "browseId", "title", "type", "year", "description",
        "audioPlaylistId", "channelId", "isExplicit"
    ]:
        if key in album:
            print(f"  {key}: {album.get(key)!r}")

    artists = album.get("artists")
    if artists is not None:
        print("  artists:")
        if isinstance(artists, list):
            for artist in artists:
                if isinstance(artist, dict):
                    print(f"    - {artist.get('name')} (id={artist.get('id')})")
                else:
                    print(f"    - {artist}")
        else:
            print(f"    {artists!r}")

    print_thumbnails("  THUMBNAILS DEL ALBUM", album.get("thumbnails"))


# ---------------------------------------------------------------------------
# 1) Consulta directa del album.id detectado en el resultado de la canción
# ---------------------------------------------------------------------------
print("[1] CONSULTANDO get_album() CON EL ALBUM ID EXACTO...")
print(f"Album ID: {ALBUM_ID}")
print()

try:
    album = ytmusic.get_album(ALBUM_ID)
except Exception as e:
    print(f"ERROR en get_album(): {e}")
    album = None

print()
print_album_summary("RESULTADO DE get_album()", album)

# Mostrar claves raíz para detectar campos no contemplados arriba.
if isinstance(album, dict):
    print("\nCLAVES DISPONIBLES EN get_album():")
    for key in album.keys():
        print(f"  - {key}")

    # Guardar solamente en memoria / consola una vista JSON legible.
    print("\nVISTA COMPLETA DEL OBJETO ALBUM (JSON):")
    try:
        print(json.dumps(album, ensure_ascii=False, indent=2))
    except TypeError:
        print(repr(album))

    # Revisar tracks y sus posibles thumbnails.
    tracks = album.get("tracks")
    print("\nTRACKS DEL ALBUM:")
    if not tracks:
        print("  No contiene tracks o la lista está vacía.")
    else:
        print(f"  Número de tracks: {len(tracks)}")
        for i, track in enumerate(tracks, 1):
            if not isinstance(track, dict):
                print(f"  [{i}] {track!r}")
                continue
            print(f"  [{i}] título={track.get('title')!r} videoId={track.get('videoId')!r}")
            if track.get("artists"):
                names = []
                for a in track.get("artists", []):
                    if isinstance(a, dict):
                        names.append(a.get("name"))
                    else:
                        names.append(str(a))
                print(f"      artistas: {', '.join(str(x) for x in names if x)}")
            print_thumbnails(f"      THUMBNAILS DEL TRACK [{i}]", track.get("thumbnails"))

# ---------------------------------------------------------------------------
# 2) Búsqueda específica de álbumes para comparar resultados
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("[2] BUSCANDO 'Pal Piso' CON filter='albums'")
print("=" * 72)

try:
    album_results = ytmusic.search(
        "Pal Piso",
        filter="albums",
        limit=10,
        ignore_spelling=True,
    )
except Exception as e:
    print(f"ERROR en search(filter='albums'): {e}")
    album_results = []

if not album_results:
    print("No se encontraron resultados de álbumes.")
else:
    for i, result in enumerate(album_results, 1):
        print(f"\nRESULTADO DE ÁLBUM #{i}")
        print(f"  category: {result.get('category')!r}")
        print(f"  resultType: {result.get('resultType')!r}")
        print(f"  title: {result.get('title')!r}")
        print(f"  browseId: {result.get('browseId')!r}")
        print(f"  type: {result.get('type')!r}")
        print(f"  year: {result.get('year')!r}")

        artists = result.get("artists")
        if artists:
            names = []
            for a in artists:
                if isinstance(a, dict):
                    names.append(a.get("name"))
                else:
                    names.append(str(a))
            print(f"  artists: {', '.join(str(x) for x in names if x)}")

        print_thumbnails("  THUMBNAILS DEL RESULTADO", result.get("thumbnails"))

        if result.get("browseId") == ALBUM_ID:
            print("  >>> ESTE RESULTADO COINCIDE EXACTAMENTE CON EL ALBUM ID DE LA CANCIÓN.")

# ---------------------------------------------------------------------------
# 3) Conclusión operativa
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("FIN DE LA PRUEBA")
print("=" * 72)
print("Recuerda: state/releases.json NO fue leído ni modificado.")
print("Lo más importante será comprobar si get_album() devuelve thumbnails distintos")
print("a los 60x60 / 120x120 que aparecieron en el resultado de la canción.")
