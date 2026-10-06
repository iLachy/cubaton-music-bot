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
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def obtener_configuracion():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token:
        raise RuntimeError(
            "Falta la variable de entorno TELEGRAM_BOT_TOKEN."
        )

    if not chat_id:
        raise RuntimeError(
            "Falta la variable de entorno TELEGRAM_CHAT_ID."
        )

    return token, chat_id


def telegram_request(token, metodo, data=None, files=None):
    url = f"{TELEGRAM_API_BASE}{token}/{metodo}"

    respuesta = requests.post(
        url,
        data=data,
        files=files,
        timeout=120
    )

    try:
        resultado = respuesta.json()
    except Exception:
        raise RuntimeError(
            f"Telegram devolvió una respuesta no JSON "
            f"(HTTP {respuesta.status_code}): {respuesta.text[:500]}"
        )

    if not respuesta.ok or not resultado.get("ok"):
        raise RuntimeError(
            f"Error de Telegram en {metodo}: {resultado}"
        )

    return resultado


def enviar_portada(token, chat_id, mensaje):
    photo = mensaje.get("photo")
    caption = mensaje.get("caption")
    parse_mode = mensaje.get("parse_mode", "HTML")

    if not photo:
        raise RuntimeError(
            "Falta la portada del mensaje 1."
        )

    if not caption:
        raise RuntimeError(
            "Falta el caption del mensaje 1."
        )

    data = {
        "chat_id": chat_id,
        "photo": photo,
        "caption": caption,
        "parse_mode": parse_mode
    }

    return telegram_request(
        token,
        "sendPhoto",
        data=data
    )


def obtener_preview_url(mensaje):
    """
    Obtiene la URL del preview aceptando las dos estructuras:

    1. audio = "https://..."
    2. audio = {
           "url": "https://...",
           "fuente": "Apple Music"
       }
    """

    audio = mensaje.get("audio")

    if isinstance(audio, dict):
        preview_url = audio.get("url")
    else:
        preview_url = audio

    if not preview_url:
        raise RuntimeError(
            "Falta el preview del mensaje 2."
        )

    return preview_url


def obtener_fuente_preview(mensaje):
    audio = mensaje.get("audio")

    if isinstance(audio, dict):
        return audio.get("fuente")

    return None


def descargar_preview(preview_url):
    print("Descargando preview...")

    respuesta = requests.get(
        preview_url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=120
    )

    if not respuesta.ok:
        raise RuntimeError(
            f"No se pudo descargar el preview. "
            f"HTTP {respuesta.status_code}"
        )

    contenido = respuesta.content

    if not contenido:
        raise RuntimeError(
            "El preview descargado está vacío."
        )

    content_type = (
        respuesta.headers.get("Content-Type", "")
        .lower()
    )

    content_disposition = (
        respuesta.headers.get("Content-Disposition", "")
        .lower()
    )

    # Apple Music normalmente devuelve M4A/AAC.
    # Deezer normalmente devuelve MP3.
    suffix = ".m4a"

    if (
        "audio/mpeg" in content_type
        or "audio/mp3" in content_type
        or ".mp3" in content_disposition
        or "filename=" in content_disposition
        and ".mp3" in content_disposition
    ):
        suffix = ".mp3"

    archivo_temporal = tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False
    )

    try:
        archivo_temporal.write(contenido)
        archivo_temporal.flush()
        ruta = Path(archivo_temporal.name)
    finally:
        archivo_temporal.close()

    print("✓ Preview descargado.")
    print(f"  Tamaño: {len(contenido)} bytes")

    return ruta


def obtener_duracion_archivo(audio_path):
    """
    Obtiene la duración REAL del archivo de preview.

    Esto es importante porque duracion_segundos representa
    la duración completa de la canción, mientras que el
    preview descargado normalmente dura unos 30 segundos.
    """

    ffprobe = shutil.which("ffprobe")

    if not ffprobe:
        raise RuntimeError(
            "No se encontró ffprobe en el sistema. "
            "Es necesario para detectar la duración real "
            "del archivo de preview."
        )

    comando = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        timeout=30
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            "ffprobe no pudo determinar la duración del preview: "
            + resultado.stderr.strip()
        )

    valor = resultado.stdout.strip()

    if not valor:
        raise RuntimeError(
            "ffprobe no devolvió una duración para el preview."
        )

    try:
        duracion = int(round(float(valor)))
    except ValueError:
        raise RuntimeError(
            f"Duración inválida devuelta por ffprobe: {valor}"
        )

    if duracion <= 0:
        raise RuntimeError(
            f"La duración real del preview es inválida: {duracion}"
        )

    return duracion


def enviar_preview(
    token,
    chat_id,
    mensaje,
    preview_path,
    preview_duration
):
    title = mensaje.get("title", "")
    performer = mensaje.get("performer", "")

    reply_markup = mensaje.get("reply_markup")

    data = {
        "chat_id": chat_id,
        "title": title,
        "performer": performer,
        "duration": str(preview_duration)
    }

    if reply_markup:
        data["reply_markup"] = json.dumps(
            reply_markup,
            ensure_ascii=False
        )

    with open(preview_path, "rb") as audio_file:
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
    if len(sys.argv) < 2:
        print(
            "Uso: python telegram_publisher.py "
            "<telegram_result.json>"
        )
        sys.exit(1)

    ruta_entrada = Path(sys.argv[1])

    if not ruta_entrada.exists():
        print(
            f"ERROR: No existe el archivo: {ruta_entrada}"
        )
        sys.exit(1)

    preview_path = None

    try:
        token, chat_id = obtener_configuracion()

        resultado = cargar_json(ruta_entrada)

        if not resultado.get("ok"):
            raise RuntimeError(
                "telegram_result.json indica que el resultado "
                "no es válido."
            )

        mensaje_1 = resultado.get("mensaje_1")
        mensaje_2 = resultado.get("mensaje_2")

        if not mensaje_1:
            raise RuntimeError(
                "Falta el mensaje 1."
            )

        if not mensaje_2:
            raise RuntimeError(
                "Falta el mensaje 2."
            )

        # =========================================================
        # MENSAJE 1
        # =========================================================

        print("PUBLICANDO PRUEBA EN TELEGRAM")
        print("1/2 Enviando portada + caption...")

        respuesta_portada = enviar_portada(
            token,
            chat_id,
            mensaje_1
        )

        mensaje_portada = respuesta_portada.get(
            "result",
            {}
        )

        print("✓ Mensaje de portada enviado.")
        print(
            f"  message_id: "
            f"{mensaje_portada.get('message_id')}"
        )

        # =========================================================
        # PREVIEW
        # =========================================================

        preview_url = obtener_preview_url(mensaje_2)
        preview_fuente = obtener_fuente_preview(mensaje_2)

        preview_path = descargar_preview(
            preview_url
        )

        if preview_fuente:
            print(
                f"  Fuente: {preview_fuente}"
            )

        # =========================================================
        # DURACIÓN REAL DEL PREVIEW
        # =========================================================

        print("")
        print(
            "Detectando duración real del preview..."
        )

        preview_duration = obtener_duracion_archivo(
            preview_path
        )

        duracion_cancion = mensaje_2.get(
            "duracion_segundos"
        )

        print("✓ Duración real del preview:")
        print(
            f"  {preview_duration} segundos"
        )

        if duracion_cancion is not None:
            print(
                "  Duración completa de la canción: "
                f"{duracion_cancion} segundos"
            )

        # =========================================================
        # MENSAJE 2
        # =========================================================

        print("")
        print(
            "2/2 Enviando preview + botón..."
        )

        respuesta_preview = enviar_preview(
            token,
            chat_id,
            mensaje_2,
            preview_path,
            preview_duration
        )

        mensaje_preview = respuesta_preview.get(
            "result",
            {}
        )

        print("✓ Mensaje de preview enviado.")
        print(
            f"  message_id: "
            f"{mensaje_preview.get('message_id')}"
        )

        # =========================================================
        # RESULTADO FINAL
        # =========================================================

        boton = None

        reply_markup = mensaje_2.get(
            "reply_markup"
        )

        if reply_markup:
            filas = reply_markup.get(
                "inline_keyboard",
                []
            )

            if filas and filas[0]:
                boton = filas[0][0]

        resultado_final = {
            "ok": True,
            "chat_id": chat_id,
            "mensaje_portada": {
                "message_id": mensaje_portada.get(
                    "message_id"
                )
            },
            "mensaje_preview": {
                "message_id": mensaje_preview.get(
                    "message_id"
                )
            },
            "preview_fuente": preview_fuente,
            "preview_duracion_segundos": preview_duration,
            "duracion_cancion_segundos": duracion_cancion,
            "boton": boton
        }

        print("")
        print(json.dumps(
            resultado_final,
            ensure_ascii=False,
            indent=2
        ))

        print("")
        print(
            "PUBLICACIÓN EN TELEGRAM EXITOSA"
        )

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    finally:
        if preview_path and preview_path.exists():
            try:
                preview_path.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    main()