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
# INFORMACIÓN GENERAL
# ============================================================

print()
print("=" * 60)
print("INFORMACIÓN DEL ARTISTA")
print("=" * 60)

print(f"Nombre: {artista.get('name')}")
print(f"Browse ID: {artista.get('channelId')}")


# ============================================================
# CONSULTAR LANZAMIENTOS CON get_artist_albums()
# ============================================================

print()
print("=" * 60)
print("CONSULTANDO get_artist_albums()")
print("=" * 60)

try:
    lanzamientos = ytmusic.get_artist_albums(ARTIST_CHANNEL_ID)

except Exception as e:
    print()
    print("ERROR AL CONSULTAR get_artist_albums():")
    print(e)
    raise SystemExit


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

print()
print("=" * 60)
print("RESULTADO DE get_artist_albums()")
print("=" * 60)

print(f"Cantidad de lanzamientos: {len(lanzamientos)}")


# ============================================================
# MOSTRAR LOS PRIMEROS LANZAMIENTOS
# ============================================================

for i, lanzamiento in enumerate(lanzamientos[:10], start=1):

    print()
    print("-" * 60)
    print(f"LANZAMIENTO #{i}")
    print("-" * 60)

    pprint(lanzamiento)


# ============================================================
# BUSCAR ESPECÍFICAMENTE ENGACHADA COMPLETA
# ============================================================

print()
print("=" * 60)
print("BUSCANDO: ENGANCHADA COMPLETA")
print("=" * 60)

encontrado = None

for lanzamiento in lanzamientos:

    titulo = str(lanzamiento.get("title", "")).lower()

    if "enganchada completa" in titulo:
        encontrado = lanzamiento
        break


if encontrado:

    print()
    print("LANZAMIENTO ENCONTRADO:")
    print()

    pprint(encontrado)

    print()
    print("=" * 60)
    print("CAMPOS DISPONIBLES")
    print("=" * 60)

    for clave, valor in encontrado.items():
        print(f"{clave}: {valor}")

else:

    print()
    print("No se encontró 'Enganchada Completa'.")


# ============================================================
# BUSCAR CUALQUIER CAMPO RELACIONADO CON FECHA
# ============================================================

print()
print("=" * 60)
print("CAMPOS RELACIONADOS CON FECHA")
print("=" * 60)

if encontrado:

    encontrados_fecha = False

    for clave, valor in encontrado.items():

        clave_lower = clave.lower()

        if (
            "date" in clave_lower
            or "year" in clave_lower
            or "time" in clave_lower
            or "release" in clave_lower
        ):
            print(f"{clave}: {valor}")
            encontrados_fecha = True

    if not encontrados_fecha:
        print("No se encontraron campos de fecha adicionales.")


print()
print("=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)
