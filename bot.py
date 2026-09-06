from ytmusicapi import YTMusic

ytmusic = YTMusic()

ARTISTS = [
    "Bebeshito",
    "Charly & Johayron",
    "Dany Ome",
    "Kevincito El 13",
    "Wampi",
    "El Taiger",
    "Ja Rulay",
    "L Kimii",
    "El Dray",
    "Ya Ice Dilan",
    "Rey Tony",
    "Baby Maykol",
    "Payaso x Ley",
    "Kaly y Kowa",
    "Wildey",
    "Wow Popy",
    "Talent Fuego",
    "Mawell",
    "Harryson",
    "El Chulo",
    "Fixty Ordara",
    "El Kamel",
    "Velito El Bufón",
    "Helabusador",
    "Un Titico",
    "Musteerifa",
    "Yordy DK",
    "Chocolate MC",
    "El Chacal",
    "El Micha",
    "Yomil",
    "Jacob Forever",
    "Gente de Zona",
    "La Diosa",
    "Seidy La Niña",
    "Srta. Dayana",
    "Divan",
    "Michel Boutic",
    "DJ Conds",
    "DJ Unic",
    "DJ Honda",
    "Roberto Ferrante",
    "Pututi",
]


def buscar_artista(nombre):
    resultados = ytmusic.search(
        nombre,
        filter="artists",
        limit=5
    )

    print()
    print("=" * 70)
    print(f"BUSQUEDA: {nombre}")
    print("=" * 70)

    if not resultados:
        print("NO SE ENCONTRARON RESULTADOS")
        return

    for i, artista in enumerate(resultados, start=1):
        print(f"{i}. Nombre: {artista.get('artist')}")
        print(f"   ID: {artista.get('browseId')}")
        print()


print("INICIANDO BUSQUEDA DE ARTISTAS EN YOUTUBE MUSIC...")
print(f"Total de artistas: {len(ARTISTS)}")

for nombre in ARTISTS:
    try:
        buscar_artista(nombre)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"ERROR BUSCANDO: {nombre}")
        print(f"Detalle: {e}")
        print("=" * 70)

print()
print("=" * 70)
print("BUSQUEDA TERMINADA")
print("=" * 70)
