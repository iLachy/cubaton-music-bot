import json
import sys
from pathlib import Path


def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def normalizar_datos(datos):
    """
    Normaliza la entrada del formatter.

    El workflow de publicación entrega un JSON con los datos
    generales de la publicación en la raíz y los datos concretos
    de la pista dentro de la clave 'track'.

    Ejemplo:

    {
        "nombre_publicacion": "LBMA",
        "fecha": "13-02-2026",
        "portada": "...",
        "track": {
            "titulo": "Te Amaré",
            "artistas": [...],
            "preview": {
                "url": "..."
            },
            "escuchar": {
                "url": "..."
            }
        }
    }

    El resultado se convierte en un único diccionario plano
    para que las funciones de construcción puedan trabajar
    siempre con la misma estructura.
    """

    if not isinstance(datos, dict):
        raise ValueError("La entrada debe ser un objeto JSON.")

    track = datos.get("track")

    if isinstance(track, dict):
        datos_normalizados = dict(datos)

        # Los datos específicos de la pista tienen prioridad.
        datos_normalizados.update(track)

        # Los datos generales de la publicación se conservan
        # si la pista no los contiene.
        if not datos_normalizados.get("nombre_publicacion"):
            datos_normalizados["nombre_publicacion"] = datos.get(
                "nombre_publicacion", ""
            )

        if not datos_normalizados.get("fecha"):
            datos_normalizados["fecha"] = datos.get("fecha", "")

        if not datos_normalizados.get("portada"):
            datos_normalizados["portada"] = datos.get("portada", "")

        if not datos_normalizados.get("deezer_album_id"):
            datos_normalizados["deezer_album_id"] = datos.get(
                "deezer_album_id"
            )

        if not datos_normalizados.get("deezer_url"):
            datos_normalizados["deezer_url"] = datos.get(
                "deezer_url", ""
            )

        return datos_normalizados

    return datos


def normalizar_artistas(artistas):
    """
    Convierte artistas en una cadena apta para Telegram.

    Acepta:
      - string
      - lista de strings
      - lista de objetos con campo 'name'
    """

    if isinstance(artistas, str):
        return artistas

    if isinstance(artistas, list):
        nombres = []

        for artista in artistas:
            if isinstance(artista, str):
                if artista.strip():
                    nombres.append(artista.strip())

            elif isinstance(artista, dict):
                nombre = (
                    artista.get("name")
                    or artista.get("nombre")
                    or artista.get("artist")
                    or ""
                )

                if nombre:
                    nombres.append(str(nombre).strip())

        return ", ".join(nombres)

    return ""


def extraer_preview(datos):
    """
    Extrae la URL del preview.

    El procesamiento actual genera:

    "preview": {
        "url": "...",
        "fuente": "Apple Music"
    }

    También mantiene compatibilidad con formatos anteriores
    donde preview podía ser directamente una cadena.
    """

    preview = datos.get("preview")

    if isinstance(preview, dict):
        return preview.get("url", "")

    if isinstance(preview, str):
        return preview

    preview_deezer = datos.get("preview_deezer")

    if isinstance(preview_deezer, dict):
        return preview_deezer.get("url", "")

    if isinstance(preview_deezer, str):
        return preview_deezer

    return ""


def extraer_duracion_segundos(datos):
    """
    Extrae la duración en segundos.

    El procesamiento actual utiliza 'duracion_segundos'.
    Se mantiene compatibilidad con formatos anteriores.
    """

    valor = datos.get("duracion_segundos")

    if valor is not None:
        try:
            return int(valor)
        except (TypeError, ValueError):
            pass

    valor = datos.get("duration")

    if valor is not None:
        try:
            return int(valor)
        except (TypeError, ValueError):
            pass

    return None


def construir_caption(datos):
    artistas = normalizar_artistas(datos.get("artistas", ""))

    titulo = (
        datos.get("titulo_publicacion")
        or datos.get("titulo")
        or ""
    )

    nombre_publicacion = datos.get("nombre_publicacion", "")
    duracion = datos.get("duracion", "")
    fecha = datos.get("fecha", "")

    # Convertir DD-MM-YYYY a DD/MM/YYYY.
    if fecha:
        try:
            partes = str(fecha).split("-")

            if len(partes) == 3:
                dia, mes, anio = partes
                fecha = f"{dia}/{mes}/{anio}"

        except Exception:
            pass

    return (
        f"🎤 {artistas}\n"
        f"<blockquote>🎵 <b>{titulo}</b></blockquote>\n"
        f"📀 <i>{nombre_publicacion}</i>\n"
        f"\n"
        f"⏳️ {duracion}\n"
        f"🗓 <b>{fecha}</b>\n"
        f"\n"
        f"<b>@Cubaton_Music</b>"
    )


def construir_mensaje_portada(datos):
    return {
        "tipo": "photo",
        "photo": datos.get("portada", ""),
        "caption": construir_caption(datos),
        "parse_mode": "HTML",
    }


def construir_mensaje_preview(datos):
    preview = extraer_preview(datos)

    # La selección definitiva de la plataforma está
    # en el objeto "escuchar" del resultado final.
    escuchar = datos.get("escuchar") or {}

    if isinstance(escuchar, dict):
        escuchar_url = escuchar.get("url", "")
        escuchar_fuente = escuchar.get("fuente", "")
    else:
        escuchar_url = ""
        escuchar_fuente = ""

    # Compatibilidad con formatos anteriores.
    if not escuchar_url:
        escuchar_url = (
            datos.get("youtube_music_url")
            or datos.get("deezer_url", "")
        )

        if datos.get("youtube_music_url"):
            escuchar_fuente = "YouTube Music"
        else:
            escuchar_fuente = "Deezer"

    if escuchar_fuente == "YouTube Music":
        boton_texto = "▶️ Escuchar en YouTube Music"
    else:
        boton_texto = "▶️ Escuchar en Deezer"

    return {
        "tipo": "audio",
        "audio": preview,
        "title": (
            datos.get("titulo_publicacion")
            or datos.get("titulo")
            or ""
        ),
        "performer": normalizar_artistas(
            datos.get("artistas", "")
        ),
        "duracion_segundos": extraer_duracion_segundos(datos),
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": boton_texto,
                        "url": escuchar_url,
                    }
                ]
            ]
        },
    }


def construir_resultado(datos):
    datos = normalizar_datos(datos)

    mensaje_1 = construir_mensaje_portada(datos)
    mensaje_2 = construir_mensaje_preview(datos)

    return {
        "ok": True,
        "mensaje_1": mensaje_1,
        "mensaje_2": mensaje_2,
    }


def main():
    if len(sys.argv) < 2:
        print(
            "Uso: python telegram_formatter.py <archivo.json>"
        )
        sys.exit(1)

    ruta_entrada = Path(sys.argv[1])

    if not ruta_entrada.exists():
        print(
            f"ERROR: No existe el archivo: {ruta_entrada}"
        )
        sys.exit(1)

    try:
        datos = cargar_json(ruta_entrada)

        resultado = construir_resultado(datos)

        print(
            json.dumps(
                resultado,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()