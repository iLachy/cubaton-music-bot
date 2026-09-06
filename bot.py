import sys
from pprint import pprint
from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN
# ============================================================

ARTIST_NAME = "Bebeshito"
ARTIST_CHANNEL_ID = "UCpVfWS-cPOE2sYqsFuuP_Qg"


# ============================================================
# PROGRAMA
# ============================================================

def main():

    print("=" * 60)
    print("DIAGNÓSTICO DE FECHA - YOUTUBE MUSIC")
    print("=" * 60)
    print()

    try:

        ytmusic = YTMusic()

        print(f"Consultando artista: {ARTIST_NAME}")
        print()

        artista = ytmusic.get_artist(
            ARTIST_CHANNEL_ID
        )

        singles = artista.get(
            "singles",
            {}
        )

        albums = artista.get(
            "albums",
            {}
        )

        lanzamiento = None

        # ----------------------------------------------------
        # Buscar el single más reciente
        # ----------------------------------------------------

        if isinstance(singles, dict):

            resultados = singles.get(
                "results",
                []
            )

            if resultados:

                lanzamiento = resultados[0]

        # ----------------------------------------------------
        # Si no hay singles, buscar álbum
        # ----------------------------------------------------

        if lanzamiento is None:

            if isinstance(albums, dict):

                resultados = albums.get(
                    "results",
                    []
                )

                if resultados:

                    lanzamiento = resultados[0]

        if lanzamiento is None:

            print("NO SE ENCONTRÓ NINGÚN LANZAMIENTO.")
            sys.exit(1)

        # ----------------------------------------------------
        # Mostrar información básica
        # ----------------------------------------------------

        print("=" * 60)
        print("LANZAMIENTO ENCONTRADO")
        print("=" * 60)

        print()
        print(
            "Título:",
            lanzamiento.get(
                "title",
                "SIN TÍTULO"
            )
        )

        print()
        print("TIPO DE OBJETO:")
        print(type(lanzamiento))

        print()
        print("=" * 60)
        print("TODOS LOS CAMPOS DEL LANZAMIENTO")
        print("=" * 60)
        print()

        pprint(
            lanzamiento,
            sort_dicts=False
        )

        # ----------------------------------------------------
        # Si tiene browseId, consultar el álbum
        # ----------------------------------------------------

        browse_id = lanzamiento.get(
            "browseId"
        )

        if browse_id:

            print()
            print("=" * 60)
            print("CONSULTANDO DETALLE DEL LANZAMIENTO")
            print("=" * 60)
            print()

            print(
                "browseId:",
                browse_id
            )

            try:

                detalle = ytmusic.get_album(
                    browse_id
                )

                print()
                print("=" * 60)
                print("TODOS LOS CAMPOS DEL DETALLE")
                print("=" * 60)
                print()

                pprint(
                    detalle,
                    sort_dicts=False
                )

            except Exception as error:

                print()
                print(
                    "No se pudo consultar "
                    "el detalle:"
                )
                print(error)

        else:

            print()
            print(
                "El lanzamiento no tiene browseId."
            )

        print()
        print("=" * 60)
        print("FIN DEL DIAGNÓSTICO")
        print("=" * 60)

    except Exception as error:

        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print()
        print(error)
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()
