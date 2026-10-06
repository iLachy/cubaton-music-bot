#!/usr/bin/env python3

import json
import sys
from html import escape


def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def construir_caption(data):
    artistas = escape(str(data.get("artistas", "")).strip())
    titulo = escape(
        str(
            data.get("titulo_publicacion")
            or data.get("titulo")
            or ""
        ).strip()
    )
    nombre_publicacion = escape(
        str(data.get("nombre_publicacion", "")).strip()
    )
    duracion = escape(str(data.get("duracion", "")).strip())
    fecha = escape(str(data.get("fecha", "")).strip())

    return (
        f"🎤 <b>{artistas}</b>\n"
        f"<blockquote>🎵 <b>{titulo}</b></blockquote>\n"
        f"📀 <i>{nombre_publicacion}</i>\n"
        f"⏳️{duracion}\n"
        f"🗓 {fecha}\n"
        f"\n"
        f"<b>@Cubaton_Music</b>"
    )


def construir_boton_escucha(data):
    escuchar = data.get("escuchar") or {}

    url = str(escuchar.get("url", "")).strip()
    fuente = str(escuchar.get("fuente", "")).strip().lower()

    if not url:
        return None

    if fuente == "youtube_music":
        texto = "▶️ Escuchar en YouTube Music"
    elif fuente == "deezer":
        texto = "▶️ Escuchar en Deezer"
    else:
        return None

    return {
        "text": texto,
        "url": url,
    }


def construir_resultado(data):
    caption = construir_caption(data)

    portada = str(data.get("portada", "")).strip()

    preview = data.get("preview") or {}
    preview_url = str(preview.get("url", "")).strip()
    preview_fuente = str(preview.get("fuente", "")).strip().lower()

    boton = construir_boton_escucha(data)

    if not portada:
        raise ValueError("No existe portada para publicar.")

    if not preview_url:
        raise ValueError("No existe preview para publicar.")

    if preview_fuente not in ("apple_music", "deezer"):
        raise ValueError(
            f"Fuente de preview no válida: {preview_fuente}"
        )

    if not boton:
        raise ValueError(
            "No existe un botón de escucha válido."
        )

    return {
        "mensaje_1": {
            "tipo": "photo",
            "photo": portada,
            "caption": caption,
            "parse_mode": "HTML",
        },
        "mensaje_2": {
            "tipo": "audio",
            "preview": preview_url,
            "preview_fuente": preview_fuente,
            "titulo": (
                data.get("titulo_publicacion")
                or data.get("titulo")
                or ""
            ),
            "artistas": data.get("artistas", ""),
            "duracion_segundos": (
                data.get("duracion_segundos")
                or 0
            ),
            "boton": boton,
        },
    }


def main():
    if len(sys.argv) != 2:
        print(
            "Uso: python telegram_formatter.py publication_result.json",
            file=sys.stderr,
        )
        sys.exit(1)

    ruta = sys.argv[1]

    try:
        data = cargar_json(ruta)
        resultado = construir_resultado(data)

        print(json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2
        ))

    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()