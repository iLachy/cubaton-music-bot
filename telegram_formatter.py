import json
import sys
from pathlib import Path


def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def construir_caption(datos):
    artistas = datos.get("artistas", "")
    titulo = datos.get("titulo_publicacion") or datos.get("titulo", "")
    nombre_publicacion = datos.get("nombre_publicacion", "")
    duracion = datos.get("duracion", "")
    fecha = datos.get("fecha", "")

    # Convertir DD-MM-YYYY → DD/MM/YYYY
    if fecha:
        try:
            partes = fecha.split("-")
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
        "parse_mode": "HTML"
    }


def construir_mensaje_preview(datos):
    preview = datos.get("preview") or datos.get("preview_deezer", "")

    boton_url = (
        datos.get("youtube_music_url")
        or datos.get("deezer_url", "")
    )

    if datos.get("youtube_music_url"):
        boton_texto = "▶️ Escuchar en YouTube Music"
    else:
        boton_texto = "▶️ Escuchar en Deezer"

    return {
        "tipo": "audio",
        "audio": preview,
        "title": datos.get("titulo_publicacion") or datos.get("titulo", ""),
        "performer": datos.get("artistas", ""),
        "duracion_segundos": datos.get("duracion_segundos"),
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": boton_texto,
                        "url": boton_url
                    }
                ]
            ]
        }
    }


def construir_resultado(datos):
    mensaje_1 = construir_mensaje_portada(datos)
    mensaje_2 = construir_mensaje_preview(datos)

    return {
        "ok": True,
        "mensaje_1": mensaje_1,
        "mensaje_2": mensaje_2
    }


def main():
    if len(sys.argv) < 2:
        print("Uso: python telegram_formatter.py <archivo.json>")
        sys.exit(1)

    ruta_entrada = Path(sys.argv[1])

    if not ruta_entrada.exists():
        print(f"ERROR: No existe el archivo: {ruta_entrada}")
        sys.exit(1)

    try:
        datos = cargar_json(ruta_entrada)
        resultado = construir_resultado(datos)

        print(json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2
        ))

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()