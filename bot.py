from ytmusicapi import YTMusic
import json

ALBUM_ID = 'MPREb_7qIBsdhyrXs'
VIDEO_ID = 'CK_t71Wx0qA'

print('\\' + '=' * 70)
print('PRUEBA SOLO DE LECTURA — ALBUM DE CONTÁNDOLE LO TIRO')
print('\\' + '=' * 70)
print()
print('state/releases.json NO será leído ni modificado.')
print('No se descargan imágenes, no se envía Telegram y no se modifica ningún archivo.')
print()

try:
    ytmusic = YTMusic()
except Exception as e:
    print('ERROR inicializando YTMusic:', repr(e))
    raise


def print_thumbnails(items, label):
    print(label)
    if not items:
        print('  No contiene thumbnails.')
        return
    for i, t in enumerate(items, 1):
        print(f"  [{i}] {t.get('width')}x{t.get('height')}")
        print(f"      {t.get('url')}")

print('[1] CONSULTANDO get_album() CON EL ALBUM ID EXACTO...')
print(f'Album ID: {ALBUM_ID}')
print()

album = ytmusic.get_album(ALBUM_ID)
print('RESULTADO DE get_album()')
print(f"  title: {album.get('title')!r}")
print(f"  type: {album.get('type')!r}")
print(f"  year: {album.get('year')!r}")
print(f"  description: {album.get('description')!r}")
print(f"  audioPlaylistId: {album.get('audioPlaylistId')!r}")
print(f"  isExplicit: {album.get('isExplicit')!r}")

artists = album.get('artists') or []
print('  artists:')
for a in artists:
    print(f"    - {a.get('name')} (id={a.get('id')})")

print_thumbnails(album.get('thumbnails'), 'THUMBNAILS DEL ALBUM')

print()
print('VISTA COMPLETA DEL OBJETO ALBUM (JSON):')
print(json.dumps(album, ensure_ascii=False, indent=2))

tracks = album.get('tracks') or []
print()
print('TRACKS DEL ALBUM:')
print(f'  Número de tracks: {len(tracks)}')
for i, track in enumerate(tracks, 1):
    print(f"  [{i}] título={track.get('title')!r} videoId={track.get('videoId')!r}")
    print('      artistas:', ', '.join(a.get('name', '') for a in (track.get('artists') or [])))
    print_thumbnails(track.get('thumbnails'), f'      THUMBNAILS DEL TRACK [{i}]')

print()
print('\\' + '=' * 70)
print('FIN DE LA PRUEBA')
print('\\' + '=' * 70)
print()
print('Recuerda: state/releases.json NO fue leído ni modificado.')
