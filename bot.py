from ytmusicapi import YTMusic

ytmusic = YTMusic()

results = ytmusic.search(
    "Bebeshito",
    filter="artists",
    limit=5
)

print("=== RESULTADOS ===")

for artist in results:
    print(f"Nombre: {artist.get('artist')}")
    print(f"ID: {artist.get('browseId')}")
    print("---")
