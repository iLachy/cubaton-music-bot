from ytmusicapi import YTMusic
import json

SONG_QUERY = "Contándole Lo Tiro Harryson Hebreo Productions"
TITLE = "Contándole Lo Tiro"
ARTISTS_EXPECTED = {"Harryson", "Hebreo Productions"}

print("=" * 72)
print("PRUEBA SOLO DE LECTURA — CONTÁNDOLE LO TIRO")
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


def artist_names(value):
    if not isinstance(value, list):
        return []
    out = []
    for a in value:
        if isinstance(a, dict):
            if a.get("name"):
                out.append(a["name"])
        elif a:
            out.append(str(a))
    return out

print("[1] BUSCANDO LA CANCIÓN CON filter='songs'")
print(f"Consulta: {SONG_QUERY}")
print()

try:
    song_results = ytmusic.search(
        SONG_QUERY,
        filter="songs",
        limit=10,
        ignore_spelling=True,
    )
except Exception as e:
    print(f"ERROR en search(filter='songs'): {e}")
    song_results = []

match = None
for i, result in enumerate(song_results, 1):
    names = artist_names(result.get("artists"))
    print(f"RESULTADO DE CANCIÓN #{i}")
    print(f"  título: {result.get('title')!r}")
    print(f"  videoId: {result.get('videoId')!r}")
    print(f"  artistas: {', '.join(names)}")
    print(f"  album: {result.get('album')!r}")
    print_thumbnails("  THUMBNAILS DEL RESULTADO", result.get("thumbnails"))
    print()

    title_ok = TITLE.casefold() in str(result.get("title") or "").casefold()
    artists_lower = {n.casefold() for n in names}
    artist_ok = ARTISTS_EXPECTED.issubset(artists_lower)
    if match is None and title_ok and artist_ok:
        match = result

if match is None:
    print("NO SE ENCONTRÓ UNA COINCIDENCIA EXACTA DE TÍTULO + ARTISTAS.")
    print("Se detiene aquí para no consultar un lanzamiento equivocado.")
    raise SystemExit(0)

print("=" * 72)
print("COINCIDENCIA ENCONTRADA")
print("=" * 72)
print(f"Título: {match.get('title')!r}")
print(f"Video ID: {match.get('videoId')!r}")
print(f"Artistas: {', '.join(artist_names(match.get('artists')))}")
print(f"Álbum: {match.get('album')!r}")
print_thumbnails("THUMBNAILS DE LA CANCIÓN", match.get("thumbnails"))

album_info = match.get("album") or {}
album_id = album_info.get("id") if isinstance(album_info, dict) else None
print(f"Album ID detectado: {album_id!r}")

if not album_id:
    print("La coincidencia no contiene album.id. No se puede hacer la prueba get_album().")
    raise SystemExit(0)

print("\n[2] CONSULTANDO get_album() CON EL ALBUM ID EXACTO")
print(f"Album ID: {album_id}")
print()

try:
    album = ytmusic.get_album(album_id)
except Exception as e:
    print(f"ERROR en get_album(): {e}")
    album = None

if not isinstance(album, dict):
    print(f"Respuesta inesperada: {album!r}")
    raise SystemExit(1)

for key in ["title", "type", "year", "trackCount", "duration", "audioPlaylistId", "isExplicit"]:
    if key in album:
        print(f"  {key}: {album.get(key)!r}")

names = artist_names(album.get("artists"))
print(f"  artists: {', '.join(names)}")
print_thumbnails("THUMBNAILS DEL ALBUM", album.get("thumbnails"))

tracks = album.get("tracks") or []
print("\nTRACKS DEL ALBUM")
print(f"  Número de tracks: {len(tracks)}")
for i, track in enumerate(tracks, 1):
    if not isinstance(track, dict):
        print(f"  [{i}] {track!r}")
        continue
    print(f"  [{i}] título={track.get('title')!r} videoId={track.get('videoId')!r}")
    print(f"      artistas: {', '.join(artist_names(track.get('artists')))}")
    print_thumbnails(f"      THUMBNAILS DEL TRACK [{i}]", track.get("thumbnails"))

print("\n[3] VISTA JSON DEL ALBUM (SOLO CONSOLA)")
try:
    print(json.dumps(album, ensure_ascii=False, indent=2))
except TypeError:
    print(repr(album))

print("\n" + "=" * 72)
print("FIN DE LA PRUEBA")
print("=" * 72)
print("state/releases.json NO fue leído ni modificado.")
print("La comparación clave será: thumbnails de la canción vs thumbnails del album")
print("y, sobre todo, qué portada de 544x544 devuelve este lanzamiento.")
