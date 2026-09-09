import os
import json
import html
import unicodedata
from io import BytesIO

import requests
from PIL import Image
from ytmusicapi import YTMusic


# ============================================================
# CONFIGURACIÓN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@Cubaton_Music"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

CANCION_OBJETIVO = "Pal Piso"
ARTISTA_OBJETIVO = "Musteerifa"
VIDEO_ID_CONOCIDO = "AU_l1Rn_nJI"  # Solo para validar el hallazgo.


# ============================================================
# UTILIDADES
# ============================================================

def escapar(texto):
    if texto is None:
        return ""
    return html.escape(str(texto))


def normalizar_nombre(nombre):
    texto = " ".join(str(nombre or "").strip().split()).casefold()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(
        c for c in texto if not unicodedata.combining(c)
    )


def extraer_artistas(objetos):
    resultado = []
    if not objetos:
        return resultado

    for artista in objetos:
        if not isinstance(artista, dict):
            continue
        nombre = artista.get("name")
        if nombre:
            resultado.append(str(nombre).strip())

    return resultado


def formatear_artistas(artistas):
    nombres = []
    vistos = set()

    for artista in artistas:
        nombre = str(artista or "").strip()
        if not nombre:
            continue

        clave = normalizar_nombre(nombre)
        if clave in vistos:
            continue

        vistos.add(clave)
        nombres.append(nombre)

    return ", ".join(nombres)


# ============================================================
# BUSCAR PAL PISO AUTOMÁTICAMENTE
# ============================================================

def buscar_pal_piso(ytmusic):
    consultas = [
        "Pal Piso",
        "Pal Piso Musteerifa",
        "Pal Piso LA R Musteerifa",
        "Pal Piso LA R Musteerifa Vittorio Di Benedetto",
    ]

    resultados_unicos = {}

    print("=" * 64)
    print("BÚSQUEDA AUTOMÁTICA DE PAL PISO")
    print("=" * 64)

    for consulta in consultas:
        print()
        print(f"Buscando: {consulta}")

        try:
            resultados = ytmusic.search(
                consulta,
                filter="songs",
                limit=20,
                ignore_spelling=True,
            )
        except Exception as error:
            print(f"ERROR en la búsqueda: {error}")
            continue

        print(f"Resultados recibidos: {len(resultados)}")

        for resultado in resultados:
            if not isinstance(resultado, dict):
                continue

            video_id = resultado.get("videoId")
            if not video_id:
                continue

            resultados_unicos[video_id] = resultado

    print()
    print(f"Resultados únicos: {len(resultados_unicos)}")

    candidatos = []

    for resultado in resultados_unicos.values():
        titulo = str(resultado.get("title") or "").strip()
        artistas = extraer_artistas(resultado.get("artists"))

        titulo_normalizado = normalizar_nombre(titulo)
        artista_objetivo_normalizado = normalizar_nombre(ARTISTA_OBJETIVO)

        titulo_coincide = (
            titulo_normalizado == normalizar_nombre(CANCION_OBJETIVO)
            or titulo_normalizado.startswith(
                normalizar_nombre(CANCION_OBJETIVO) + " "
            )
            or titulo_normalizado.startswith(
                normalizar_nombre(CANCION_OBJETIVO) + " ("
            )
        )

        tiene_musteerifa = any(
            normalizar_nombre(artista) == artista_objetivo_normalizado
            for artista in artistas
        )

        if titulo_coincide and tiene_musteerifa:
            candidatos.append(resultado)

    if not candidatos:
        return None

    # Priorizar el ID que conocemos solo para validar que la búsqueda
    # automática encontró exactamente el lanzamiento esperado.
    candidatos.sort(
        key=lambda r: (
            1 if r.get("videoId") == VIDEO_ID_CONOCIDO else 0,
            1 if normalizar_nombre(r.get("title")) == normalizar_nombre(CANCION_OBJETIVO) else 0,
        ),
        reverse=True,
    )

    encontrado = candidatos[0]

    print()
    print("=" * 64)
    print("LANZAMIENTO ENCONTRADO AUTOMÁTICAMENTE")
    print("=" * 64)
    print(f"Título:      {encontrado.get('title')}")
    print(f"Video ID:    {encontrado.get('videoId')}")
    print(
        f"Artistas:    "
        f"{formatear_artistas(extraer_artistas(encontrado.get('artists')))}"
    )

    album = encontrado.get("album") or {}
    album_id = album.get("id") or album.get("browseId")
    print(f"Album ID:    {album_id or '(vacío)'}")

    return encontrado


# ============================================================
# COMPLETAR DATOS MEDIANTE GET_ALBUM
# ============================================================

def preparar_cancion(ytmusic, resultado):
    video_id = resultado.get("videoId")
    titulo = resultado.get("title")

    artistas = extraer_artistas(resultado.get("artists"))
    if not artistas:
        artistas = [ARTISTA_OBJETIVO]

    album = resultado.get("album") or {}
    album_id = album.get("id") or album.get("browseId")

    if not album_id:
        return None, "El resultado no tiene album.id/browseId."

    try:
        print()
        print("=" * 64)
        print("OBTENIENDO METADATOS COMPLETOS DEL LANZAMIENTO")
        print("=" * 64)
        print(f"Album ID: {album_id}")

        datos_album = ytmusic.get_album(album_id)

    except Exception as error:
        return None, f"No se pudo ejecutar get_album(): {error}"

    if not datos_album:
        return None, "get_album() no devolvió datos."

    anio = str(datos_album.get("year") or "")
    tipo = str(datos_album.get("type") or "Single").strip()

    if tipo.casefold() == "ep":
        tipo = "EP"
    elif tipo.casefold() in ("album", "álbum"):
        tipo = "Album"
    else:
        tipo = "Single"

    thumbnails = datos_album.get("thumbnails") or []
    thumbnails_validas = [
        x for x in thumbnails
        if isinstance(x, dict) and x.get("url")
    ]

    if not thumbnails_validas:
        return None, "El lanzamiento no contiene thumbnails válidas."

    portada = max(
        thumbnails_validas,
        key=lambda x: (
            int(x.get("width") or 0),
            int(x.get("height") or 0),
        ),
    )

    cancion = {
        "video_id": video_id,
        "titulo": titulo,
        "artistas": formatear_artistas(artistas),
        "tipo": tipo,
        "anio": anio,
        "nombre_publicacion": "Single" if tipo == "Single" else str(
            datos_album.get("title") or album.get("name") or titulo
        ),
        "youtube_url": f"https://music.youtube.com/watch?v={video_id}",
        "album_browse_id": album_id,
        "thumbnail_url": portada["url"],
    }

    print(f"Título álbum: {datos_album.get('title')}")
    print(f"Tipo álbum:   {tipo}")
    print(f"Año:          {anio or '(vacío)'}")
    print(
        f"Portada:      {portada.get('width')}x{portada.get('height')}"
    )
    print(f"URL portada:  {portada['url']}")

    return cancion, None


# ============================================================
# PUBLICAR SIN TOCAR STATE
# ============================================================

def publicar_pal_piso(cancion):
    titulo = escapar(cancion["titulo"])
    artistas = escapar(cancion["artistas"])
    nombre_publicacion = escapar(cancion["nombre_publicacion"])
    anio = escapar(cancion["anio"])

    caption = (
        f"🎤 <b>{artistas}</b>\n"
        f"<blockquote>🎵 <b>{titulo}</b></blockquote>\n"
        f"📀 <i>{nombre_publicacion}</i>\n"
        f"🗓 {anio}\n"
        f"\n"
        f"@Cubaton_Music"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "▶️ Escuchar en YouTube Music",
                    "url": cancion["youtube_url"],
                }
            ]
        ]
    }

    print()
    print("=" * 64)
    print("PREPARANDO PUBLICACIÓN")
    print("=" * 64)
    print(caption)

    try:
        print()
        print("Descargando portada desde YouTube Music...")

        respuesta_imagen = requests.get(
            cancion["thumbnail_url"],
            timeout=30,
        )
        respuesta_imagen.raise_for_status()

        buffer = BytesIO(respuesta_imagen.content)
        buffer.seek(0)

        imagen = Image.open(buffer)
        print(
            f"Dimensiones reales de la portada: "
            f"{imagen.width}x{imagen.height}"
        )
        print(f"Formato real: {imagen.format}")

        buffer.seek(0)

    except Exception as error:
        return False, f"No se pudo preparar la portada: {error}"

    try:
        print()
        print("Enviando a Telegram...")

        respuesta = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(
                    reply_markup,
                    ensure_ascii=False,
                ),
            },
            files={
                "photo": (
                    f"{cancion['video_id']}.jpg",
                    buffer,
                    "image/jpeg",
                )
            },
            timeout=60,
        )

        if not respuesta.ok:
            return False, respuesta.text

        datos = respuesta.json()

        if not datos.get("ok"):
            return False, str(datos)

        return True, None

    except Exception as error:
        return False, str(error)


# ============================================================
# MAIN DE PRUEBA
# ============================================================

def main():
    print("=" * 64)
    print("PRUEBA CONTROLADA: PAL PISO")
    print("NO MODIFICA state/releases.json")
    print("PUBLICA SOLAMENTE PAL PISO")
    print("=" * 64)

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No existe TELEGRAM_BOT_TOKEN.")
        return

    ytmusic = YTMusic()

    resultado = buscar_pal_piso(ytmusic)

    if not resultado:
        print()
        print("NO SE ENCONTRÓ PAL PISO AUTOMÁTICAMENTE.")
        print("No se publicará nada.")
        print("State modificado: NO")
        return

    if resultado.get("videoId") == VIDEO_ID_CONOCIDO:
        print()
        print("VALIDACIÓN: la búsqueda automática encontró el videoId esperado.")
    else:
        print()
        print(
            "ADVERTENCIA: se encontró una coincidencia de Pal Piso, "
            "pero no coincide con el videoId conocido."
        )

    cancion, error = preparar_cancion(ytmusic, resultado)

    if not cancion:
        print()
        print(f"ERROR PREPARANDO LA CANCIÓN: {error}")
        print("No se publicará nada.")
        print("State modificado: NO")
        return

    exito, error = publicar_pal_piso(cancion)

    print()
    print("=" * 64)
    print("RESULTADO DE LA PRUEBA")
    print("=" * 64)

    if exito:
        print("PUBLICADA CORRECTAMENTE")
    else:
        print("ERROR AL PUBLICAR")
        print(error)

    print("State modificado: NO")
    print("=" * 64)


if __name__ == "__main__":
    main()
