from ytmusicapi import YTMusic
from pprint import pprint


# ============================================================
# CONFIGURACIÓN
# ============================================================

ARTIST_NAME = "Bebeshito"
ARTIST_CHANNEL_ID = "UCpVfWS-cPOE2sYqsFuuP_Qg"


# ============================================================
# INICIALIZAR YOUTUBE MUSIC
# ============================================================

ytmusic = YTMusic()


# ============================================================
# CONSULTAR ARTISTA
# ============================================================

print(f"Consultando artista: {ARTIST_NAME}")

artista = ytmusic.get_artist(ARTIST_CHANNEL_ID)


# ============================================================
# BUSCAR EL LANZAMIENTO MÁS RECIENTE
# ============================================================

lanzamientos = []

if "singles" in artista:
    lanzamientos.extend(artista["singles"].get("results", []))

if "albums" in artista:
    lanzamientos.extend(artista["albums"].get("results", []))


if not lanzamientos:
    print("No se encontraron lanzamientos.")
    raise SystemExit


# Tomamos el primero, que corresponde al más reciente
lanzamiento = lanzamientos[0]

print()
print("=" * 60)
print("LANZAMIENTO ENCONTRADO")
print("=" * 60)

print(f"Título: {lanzamiento.get('title')}")
print(f"Tipo: {lanzamiento.get('type')}")
print(f"Año: {lanzamiento.get('year')}")
print(f"Browse ID: {lanzamiento.get('browseId')}")


# ============================================================
# CONSULTAR DETALLE DEL LANZAMIENTO
# ============================================================

browse_id = lanzamiento.get("browseId")

if not browse_id:
    print()
    print("El lanzamiento no tiene browseId.")
    raise SystemExit


print()
print("=" * 60)
print("CONSULTANDO DETALLE DEL LANZAMIENTO")
print("=" * 60)

detalle = ytmusic.get_album(browse_id)


# ============================================================
# BUSCAR VIDEO ID
# ============================================================

tracks = detalle.get("tracks", [])

if not tracks:
    print()
    print("El lanzamiento no contiene tracks.")
    raise SystemExit


track = tracks[0]

video_id = track.get("videoId")


print()
print("=" * 60)
print("TRACK ENCONTRADO")
print("=" * 60)

print(f"Título: {track.get('title')}")
print(f"Video ID: {video_id}")


if not video_id:
    print()
    print("No se encontró videoId.")
    raise SystemExit


# ============================================================
# CONSULTAR INFORMACIÓN DEL VIDEO
# ============================================================

print()
print("=" * 60)
print("CONSULTANDO get_song()")
print("=" * 60)

try:
    song = ytmusic.get_song(video_id)

except Exception as e:
    print()
    print("ERROR AL CONSULTAR get_song():")
    print(e)
    raise SystemExit


# ============================================================
# MOSTRAR TODOS LOS CAMPOS
# ============================================================

print()
print("=" * 60)
print("TODOS LOS CAMPOS DE get_song()")
print("=" * 60)

pprint(song)


# ============================================================
# BUSCAR FECHAS
# ============================================================

print()
print("=" * 60)
print("FECHAS ENCONTRADAS")
print("=" * 60)

print(f"publishDate: {song.get('publishDate')}")
print(f"uploadDate: {song.get('uploadDate')}")


# ============================================================
# MOSTRAR POSIBLES CAMPOS DE METADATOS
# ============================================================

print()
print("=" * 60)
print("CAMPOS RELACIONADOS CON FECHA")
print("=" * 60)

for clave, valor in song.items():

    if "date" in clave.lower() or "time" in clave.lower():
        print(f"{clave}: {valor}")
