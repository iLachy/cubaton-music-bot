#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests


TELEGRAM_API_BASE = "https://api.telegram.org/bot"


def cargar_json(ruta):

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def obtener_configuracion():

    token = os.getenv(
        "TELEGRAM_BOT_TOKEN",
        ""
    ).strip()

    chat_id = os.getenv(
        "TELEGRAM_CHAT_ID",
        ""
    ).strip()

    if not token:

        raise RuntimeError(
            "Falta el secret TELEGRAM_BOT_TOKEN."
        )

    if not chat_id:

        raise RuntimeError(
            "Falta el secret TELEGRAM_CHAT_ID."
        )

    return token, chat_id


def telegram_request(
    token,
    method,
    data=None,
    files=None
):

    url = (
        f"{TELEGRAM_API_BASE}"
        f"{token}/{method}"
    )

    response = requests.post(
        url,
        data=data,
        files=files,
        timeout=60
    )

    try:

        result = response.json()

    except ValueError:

        raise RuntimeError(
            "Telegram devolvió una respuesta "
            f"no JSON. HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    if (
        not response.ok
        or not result.get("ok")
    ):

        error_code = result.get(
            "error_code",
            response.status_code
        )

        description = result.get(
            "description",
            "Error desconocido de Telegram."
        )

        raise RuntimeError(
            f"Telegram API error "
            f"{error_code}: {description}"
        )

    return result["result"]


def enviar_portada(
    token,
    chat_id,
    mensaje
):

    data = {
        "chat_id": chat_id,
        "photo": mensaje["photo"],
        "caption": mensaje["caption"],
        "parse_mode": mensaje.get(
            "parse_mode",
            "HTML"
        )
    }

    return telegram_request(
        token,
        "sendPhoto",
        data=data
    )


def descargar_preview(url):

    response = requests.get(
        url,
        stream=True,
        timeout=60,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    if not response.ok:

        raise RuntimeError(
            "No se pudo descargar el preview. "
            f"HTTP {response.status_code}"
        )

    content_type = (
        response.headers.get(
            "Content-Type",
            ""
        ).lower()
    )

    if (
        not content_type.startswith("audio/")
        and
        "octet-stream" not in content_type
    ):

        print(
            "ADVERTENCIA: El servidor del preview "
            f"devolvió Content-Type: {content_type}"
        )

    suffix = ".m4a"

    content_disposition = (
        response.headers.get(
            "Content-Disposition",
            ""
        ).lower()
    )

    if ".mp3" in content_disposition:

        suffix = ".mp3"

    elif ".m4a" in content_disposition:

        suffix = ".m4a"

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    )

    temp_path = Path(
        temp.name
    )

    try:

        for chunk in response.iter_content(
            chunk_size=64 * 1024
        ):

            if chunk:

                temp.write(chunk)

        temp.close()

        size = temp_path.stat().st_size

        if size <= 0:

            raise RuntimeError(
                "El preview descargado está vacío."
            )

        return temp_path

    except Exception:

        try:
            temp.close()
        except Exception:
            pass

        try:
            temp_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass

        raise


def obtener_duracion_archivo(
    audio_path
):

    """
    Obtiene la duración REAL del archivo de
    preview descargado.

    Se utiliza ffprobe porque permite leer
    correctamente M4A/MP4 y MP3 sin modificar
    el archivo.

    Devuelve la duración redondeada al segundo.
    """

    ffprobe = shutil.which(
        "ffprobe"
    )

    if not ffprobe:

        raise RuntimeError(
            "No se encontró ffprobe en el runner. "
            "Es necesario para determinar la duración "
            "real del preview."
        )

    command = [

        ffprobe,

        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(audio_path)
    ]

    process = subprocess.run(

        command,

        capture_output=True,

        text=True
    )


    if process.returncode != 0:

        error = (
            process.stderr
            or
            "Error desconocido."
        ).strip()

        raise RuntimeError(
            "ffprobe no pudo determinar la duración "
            f"del preview: {error}"
        )


    raw_duration = (
        process.stdout
        or ""
    ).strip()


    try:

        duration_seconds = float(
            raw_duration
        )

    except (
        TypeError,
        ValueError
    ):

        raise RuntimeError(
            "ffprobe devolvió una duración inválida: "
            f"{raw_duration}"
        )


    if duration_seconds <= 0:

        raise RuntimeError(
            "La duración real del preview debe ser "
            "mayor que cero."
        )


    duration_integer = int(
        round(
            duration_seconds
        )
    )


    if duration_integer <= 0:

        duration_integer = 1


    return duration_integer


def enviar_preview(
    token,
    chat_id,
    mensaje,
    preview_path,
    preview_duration
):

    boton = mensaje["boton"]

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": boton["text"],
                    "url": boton["url"]
                }
            ]
        ]
    }

    data = {
        "chat_id": chat_id,

        "title": str(
            mensaje.get(
                "titulo",
                ""
            )
        ).strip()[:64],

        "performer": str(
            mensaje.get(
                "artistas",
                ""
            )
        ).strip()[:64],

        "duration": str(
            preview_duration
        ),

        "reply_markup": json.dumps(
            reply_markup,
            ensure_ascii=False
        )
    }


    with open(
        preview_path,
        "rb"
    ) as audio_file:

        files = {
            "audio": (
                preview_path.name,
                audio_file,
                "audio/mp4"
            )
        }

        return telegram_request(
            token,
            "sendAudio",
            data=data,
            files=files
        )


def main():

    if len(sys.argv) != 2:

        print(
            "Uso: python telegram_publisher.py "
            "telegram_result.json",
            file=sys.stderr
        )

        sys.exit(1)

    ruta = sys.argv[1]

    preview_path = None

    try:

        token, chat_id = (
            obtener_configuracion()
        )

        data = cargar_json(
            ruta
        )

        mensaje_1 = data[
            "mensaje_1"
        ]

        mensaje_2 = data[
            "mensaje_2"
        ]

        print(
            "========================================"
        )

        print(
            "PUBLICACIÓN DE TELEGRAM"
        )

        print(
            "========================================"
        )

        # ====================================
        # MENSAJE 1
        # ====================================

        print("")
        print(
            "1/2 Enviando portada + caption..."
        )

        resultado_foto = enviar_portada(
            token,
            chat_id,
            mensaje_1
        )

        photo_message_id = (
            resultado_foto[
                "message_id"
            ]
        )

        print(
            "✓ Mensaje de portada enviado."
        )

        print(
            f"  message_id: "
            f"{photo_message_id}"
        )

        # ====================================
        # PREVIEW
        # ====================================

        print("")
        print(
            "Descargando preview..."
        )

        preview_path = descargar_preview(
            mensaje_2["preview"]
        )

        preview_size = (
            preview_path.stat().st_size
        )

        print(
            "✓ Preview descargado."
        )

        print(
            f"  Tamaño: "
            f"{preview_size} bytes"
        )

        print(
            f"  Fuente: "
            f"{mensaje_2['preview_fuente']}"
        )

        # ====================================
        # DURACIÓN REAL DEL PREVIEW
        # ====================================

        print("")
        print(
            "Detectando duración real del preview..."
        )

        preview_duration = (
            obtener_duracion_archivo(
                preview_path
            )
        )

        print(
            "✓ Duración real del preview:"
        )

        print(
            f"  {preview_duration} segundos"
        )

        # Mostrar también la duración completa
        # para dejar claro que son valores diferentes.

        duracion_cancion = (
            mensaje_2.get(
                "duracion_segundos"
            )
        )

        if duracion_cancion:

            print(
                "  Duración completa de la canción:"
                f" {duracion_cancion} segundos"
            )

        # ====================================
        # MENSAJE 2
        # ====================================

        print("")
        print(
            "2/2 Enviando preview + botón..."
        )

        resultado_audio = enviar_preview(
            token,
            chat_id,
            mensaje_2,
            preview_path,
            preview_duration
        )

        audio_message_id = (
            resultado_audio[
                "message_id"
            ]
        )

        print(
            "✓ Mensaje de preview enviado."
        )

        print(
            f"  message_id: "
            f"{audio_message_id}"
        )

        # ====================================
        # RESULTADO
        # ====================================

        resultado_final = {

            "ok": True,

            "chat_id": chat_id,

            "mensaje_portada": {
                "message_id":
                    photo_message_id
            },

            "mensaje_preview": {
                "message_id":
                    audio_message_id
            },

            "preview_fuente":
                mensaje_2[
                    "preview_fuente"
                ],

            "preview_duracion_segundos":
                preview_duration,

            "duracion_cancion_segundos":
                duracion_cancion,

            "boton":
                mensaje_2[
                    "boton"
                ]
        }

        print("")
        print(
            json.dumps(
                resultado_final,
                ensure_ascii=False,
                indent=2
            )
        )

        print("")
        print(
            "========================================"
        )

        print(
            "PUBLICACIÓN EN TELEGRAM EXITOSA"
        )

        print(
            "========================================"
        )

    except Exception as exc:

        print("")
        print(
            "========================================"
        )

        print(
            "ERROR EN LA PUBLICACIÓN DE TELEGRAM"
        )

        print(
            "========================================"
        )

        print(
            str(exc)
        )

        print(
            "========================================"
        )

        sys.exit(1)

    finally:

        if preview_path:

            try:

                preview_path.unlink(
                    missing_ok=True
                )

            except Exception:

                pass


if __name__ == "__main__":
    main()