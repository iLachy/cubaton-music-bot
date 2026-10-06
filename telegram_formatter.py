#!/usr/bin/env python3

import json
import sys


def cargar_resultado(ruta):
    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def construir_texto_publicacion(data):
    artistas = (
        data.get("artistas")
        or ""
    )

    titulo = (
        data.get("titulo_publicacion")
        or data.get("titulo")
        or ""
    )

    nombre_publicacion = (
        data.get("nombre_publicacion")
        or ""
    )

    duracion = (
        data.get("duracion")
        or ""
    )

    fecha = (
        data.get("fecha")
        or ""
    )

    return (
        f"🎤 {artistas}\n"
        f"🎵 {titulo}\n"
        f"📀 {nombre_publicacion}\n"
        f"⏳️ {duracion}\n"
        f"🗓 {fecha}"
    )


def construir_botones(data):
    botones = []

    escuchar = (
        data.get("escuchar")
        or {}
    )

    escuchar_url = (
        escuchar.get("url")
        or ""
    )

    escuchar_fuente = (
        escuchar.get("fuente")
        or ""
    )

    if escuchar_url:

        if escuchar_fuente == "YouTube Music":

            texto = "▶️ Escuchar en YouTube Music"

        elif escuchar_fuente == "Deezer":

            texto = "▶️ Escuchar en Deezer"

        else:

            texto = "▶️ Escuchar"

        botones.append(
            {
                "text": texto,
                "url": escuchar_url
            }
        )

    apple_music = (
        data.get("apple_music")
        or {}
    )

    apple_url = (
        apple_music.get("url")
        or ""
    )

    if apple_url:

        botones.append(
            {
                "text": " Apple Music",
                "url": apple_url
            }
        )

    deezer_url = (
        data.get("deezer_url")
        or ""
    )

    if deezer_url:

        botones.append(
            {
                "text": "🎧 Deezer",
                "url": deezer_url
            }
        )

    return botones


def construir_salida(data):
    texto = construir_texto_publicacion(data)

    botones = construir_botones(data)

    return {
        "texto": texto,
        "botones": botones
    }


def main():

    if len(sys.argv) < 2:

        print(
            "Uso: python telegram_formatter.py publication_result.json",
            file=sys.stderr
        )

        sys.exit(1)

    ruta = sys.argv[1]

    try:

        data = cargar_resultado(ruta)

    except Exception as e:

        print(
            f"ERROR: No se pudo leer {ruta}: {e}",
            file=sys.stderr
        )

        sys.exit(1)

    if not isinstance(data, dict):

        print(
            "ERROR: El resultado debe ser un objeto JSON.",
            file=sys.stderr
        )

        sys.exit(1)

    salida = construir_salida(data)

    print(
        json.dumps(
            salida,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()