#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
telegram_publisher.py

Publicador de Telegram para los mensajes generados por
telegram_formatter.py.

Funcionamiento:

Modo tradicional:
    python telegram_publisher.py telegram_result.json

Modo con estado persistente:
    python telegram_publisher.py telegram_result.json \
        --state-file data/publication_state.json \
        --deezer-album-id 917540341 \
        --deezer-track-id 3839609781 \
        --track-index 1 \
        --tipo EP \
        --nombre-publicacion LBMA \
        --fecha 13-02-2026 \
        --portada "https://..."

En modo con estado:

1. Comprueba si la portada ya fue enviada.
2. Si no fue enviada, la publica.
3. Guarda inmediatamente su message_id.
4. Comprueba si el preview ya fue enviado.
5. Si no fue enviado, descarga el preview.
6. Lo publica.
7. Guarda inmediatamente su message_id.
8. Marca la pista como completed.
9. Actualiza el estado del release.

Si el proceso falla entre dos mensajes, una ejecución posterior
puede continuar sin duplicar el mensaje que ya fue enviado.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

from publication_state import (
    cargar_estado,
    crear_o_actualizar_pista,
    crear_o_actualizar_release,
    guardar_estado,
    obtener_pista,
    obtener_release,
    registrar_portada_enviada,
    registrar_preview_enviada,
    actualizar_estado_release,
    portada_enviada,
    preview_enviada,
)


TELEGRAM_API_BASE = "https://api.telegram.org/bot"

VERSION = "2026-10-07-publication-state-v1"


# ============================================================
# JSON
# ============================================================

def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


# ============================================================
# ARGUMENTOS
# ============================================================

def obtener_argumentos():
    parser = argparse.ArgumentParser(
        description=(
            "Publica los mensajes de Telegram generados por "
            "telegram_formatter.py."
        )
    )

    parser.add_argument(
        "telegram_result",
        help="Ruta al archivo telegram_result.json."
    )

    parser.add_argument(
        "--state-file",
        default=None,
        help=(
            "Ruta al archivo publication_state.json. "
            "Si se proporciona, se activa el estado persistente."
        )
    )

    parser.add_argument(
        "--deezer-album-id",
        default=None,
        help="ID del álbum/release en Deezer."
    )

    parser.add_argument(
        "--deezer-track-id",
        default=None,
        help="ID de la pista en Deezer."
    )

    parser.add_argument(
        "--track-index",
        type=int,
        default=None,
        help="Número de pista dentro del release."
    )

    parser.add_argument(
        "--tipo",
        default=None,
        help="Tipo de release: single, EP, album, etc."
    )

    parser.add_argument(
        "--nombre-publicacion",
        default=None,
        help="Nombre de la publicación/release."
    )

    parser.add_argument(
        "--fecha",
        default=None,
        help="Fecha del release."
    )

    parser.add_argument(
        "--portada",
        default=None,
        help="URL de portada del release."
    )

    return parser.parse_args()


# ============================================================
# CONFIGURACIÓN TELEGRAM
# ============================================================

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


# ============================================================
# TELEGRAM API
# ============================================================

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
            f"(HTTP {respuesta.status_code}): "
            f"{respuesta.text[:500]}"
        )

    if not respuesta.ok or not resultado.get("ok"):
        raise RuntimeError(
            f"Error de Telegram en {metodo}: {resultado}"
        )

    return resultado


# ============================================================
# MENSAJE DE PORTADA
# ============================================================

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


# ============================================================
# PREVIEW
# ============================================================

def obtener_preview_url(mensaje):
    """
    Obtiene la URL del preview.

    Estructura actual:

        "audio": {
            "url": "https://...",
            "fuente": "Apple Music"
        }

    También acepta:

        "audio": "https://..."

    Y como compatibilidad:

        "preview": "https://..."
    """

    audio = mensaje.get("audio")

    if isinstance(audio, dict):
        preview_url = audio.get("url")

        if preview_url:
            return preview_url

    if isinstance(audio, str) and audio.strip():
        return audio.strip()

    preview = mensaje.get("preview")

    if isinstance(preview, str) and preview.strip():
        return preview.strip()

    raise RuntimeError(
        "Falta el preview del mensaje 2."
    )


def obtener_fuente_preview(mensaje):
    audio = mensaje.get("audio")

    if isinstance(audio, dict):
        fuente = audio.get("fuente")

        if fuente:
            return fuente

    return mensaje.get("preview_fuente")


# ============================================================
# DESCARGA DEL PREVIEW
# ============================================================

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
        respuesta.headers.get(
            "Content-Type",
            ""
        ).lower()
    )

    content_disposition = (
        respuesta.headers.get(
            "Content-Disposition",
            ""
        ).lower()
    )

    suffix = ".m4a"

    if (
        "audio/mpeg" in content_type
        or "audio/mp3" in content_type
        or ".mp3" in content_disposition
    ):
        suffix = ".mp3"

    archivo_temporal = tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False
    )

    try:
        archivo_temporal.write(contenido)
        archivo_temporal.flush()

        ruta = Path(
            archivo_temporal.name
        )

    finally:
        archivo_temporal.close()

    print("✓ Preview descargado.")

    print(
        f"  Tamaño: {len(contenido)} bytes"
    )

    return ruta


# ============================================================
# DURACIÓN REAL
# ============================================================

def obtener_duracion_archivo(audio_path):
    """
    Obtiene la duración REAL del archivo descargado.

    No utiliza la duración de la canción completa.
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
            "ffprobe no pudo determinar la duración "
            "del preview: "
            + resultado.stderr.strip()
        )

    valor = resultado.stdout.strip()

    if not valor:
        raise RuntimeError(
            "ffprobe no devolvió una duración "
            "para el preview."
        )

    try:
        duracion = int(
            round(float(valor))
        )

    except ValueError:
        raise RuntimeError(
            f"Duración inválida devuelta por "
            f"ffprobe: {valor}"
        )

    if duracion <= 0:
        raise RuntimeError(
            f"La duración real del preview "
            f"es inválida: {duracion}"
        )

    return duracion


# ============================================================
# MENSAJE DE PREVIEW
# ============================================================

def enviar_preview(
    token,
    chat_id,
    mensaje,
    preview_path,
    preview_duration
):
    title = mensaje.get(
        "title",
        ""
    )

    performer = mensaje.get(
        "performer",
        ""
    )

    reply_markup = mensaje.get(
        "reply_markup"
    )

    data = {
        "chat_id": chat_id,
        "title": title,
        "performer": performer,
        "duration": str(
            preview_duration
        )
    }

    if reply_markup:
        data["reply_markup"] = json.dumps(
            reply_markup,
            ensure_ascii=False
        )

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


# ============================================================
# ESTADO PERSISTENTE
# ============================================================

def configurar_estado(args, telegram_result):
    """
    Carga y prepara el estado persistente.

    Devuelve:

        (estado, release, pista)

    o:

        (None, None, None)

    si no se proporcionó --state-file.
    """

    if not args.state_file:
        return None, None, None

    if not args.deezer_album_id:
        raise RuntimeError(
            "Cuando se utiliza --state-file también es "
            "obligatorio --deezer-album-id."
        )

    if not args.deezer_track_id:
        raise RuntimeError(
            "Cuando se utiliza --state-file también es "
            "obligatorio --deezer-track-id."
        )

    state_file = Path(
        args.state_file
    )

    estado = cargar_estado(
        state_file
    )

    # --------------------------------------------------------
    # Datos generales de la publicación.
    # --------------------------------------------------------

    release = crear_o_actualizar_release(
        estado,
        deezer_album_id=args.deezer_album_id,
        deezer_url=telegram_result.get(
            "deezer_url"
        ),
        tipo=args.tipo,
        nombre_publicacion=args.nombre_publicacion,
        fecha=args.fecha,
        portada=args.portada,
        total_pistas=telegram_result.get(
            "total_pistas"
        )
    )

    # --------------------------------------------------------
    # Datos de la pista.
    # --------------------------------------------------------

    mensaje_2 = telegram_result.get(
        "mensaje_2",
        {}
    )

    pista = crear_o_actualizar_pista(
        release,
        deezer_track_id=args.deezer_track_id,
        index=args.track_index,
        titulo=mensaje_2.get("title"),
        titulo_publicacion=mensaje_2.get("title"),
        artistas=mensaje_2.get("performer"),
        duracion_segundos=mensaje_2.get(
            "duracion_segundos"
        ),
        isrc=telegram_result.get(
            "isrc"
        )
    )

    guardar_estado(
        estado,
        state_file
    )

    return estado, release, pista


def guardar_estado_actual(
    estado,
    state_file,
    release
):
    """
    Actualiza el estado del release y lo guarda inmediatamente.
    """

    actualizar_estado_release(
        release
    )

    guardar_estado(
        estado,
        state_file
    )


# ============================================================
# RESULTADO FINAL
# ============================================================

def obtener_boton(mensaje_2):
    boton = None

    reply_markup = (
        mensaje_2.get(
            "reply_markup"
        )
    )

    if reply_markup:
        filas = (
            reply_markup.get(
                "inline_keyboard",
                []
            )
        )

        if filas and filas[0]:
            boton = filas[0][0]

    return boton


# ============================================================
# MAIN
# ============================================================

def main():

    args = obtener_argumentos()

    ruta_entrada = Path(
        args.telegram_result
    )

    if not ruta_entrada.exists():
        print(
            f"ERROR: No existe el archivo: "
            f"{ruta_entrada}"
        )

        sys.exit(1)

    preview_path = None

    try:

        # =====================================================
        # IDENTIFICACIÓN
        # =====================================================

        print(
            "telegram_publisher.py"
        )

        print(
            f"Versión: {VERSION}"
        )

        print(
            "========================================"
        )

        # =====================================================
        # CONFIGURACIÓN
        # =====================================================

        token, chat_id = (
            obtener_configuracion()
        )

        resultado = cargar_json(
            ruta_entrada
        )

        if not resultado.get("ok"):
            raise RuntimeError(
                "telegram_result.json indica "
                "que el resultado no es válido."
            )

        mensaje_1 = resultado.get(
            "mensaje_1"
        )

        mensaje_2 = resultado.get(
            "mensaje_2"
        )

        if not mensaje_1:
            raise RuntimeError(
                "Falta el mensaje 1."
            )

        if not mensaje_2:
            raise RuntimeError(
                "Falta el mensaje 2."
            )

        # =====================================================
        # ESTADO PERSISTENTE
        # =====================================================

        estado = None
        release = None
        pista = None
        state_file = None

        if args.state_file:

            print("")
            print(
                "MODO DE ESTADO PERSISTENTE: ACTIVADO"
            )

            print(
                f"  Archivo: {args.state_file}"
            )

            print(
                f"  Deezer album ID: "
                f"{args.deezer_album_id}"
            )

            print(
                f"  Deezer track ID: "
                f"{args.deezer_track_id}"
            )

            if args.track_index is not None:
                print(
                    f"  Índice: {args.track_index}"
                )

            state_file = Path(
                args.state_file
            )

            estado, release, pista = (
                configurar_estado(
                    args,
                    resultado
                )
            )

            print(
                f"  Estado actual de la pista: "
                f"{pista.get('estado')}"
            )

            print(
                f"  Portada enviada: "
                f"{portada_enviada(pista)}"
            )

            print(
                f"  Preview enviada: "
                f"{preview_enviada(pista)}"
            )

        else:

            print("")
            print(
                "MODO DE ESTADO PERSISTENTE: DESACTIVADO"
            )

        # =====================================================
        # MENSAJE 1 — PORTADA
        # =====================================================

        print("")
        print(
            "PUBLICANDO EN TELEGRAM"
        )

        portada_message_id = None

        if (
            pista is not None
            and portada_enviada(pista)
        ):

            portada_message_id = (
                pista["portada"]["message_id"]
            )

            print(
                "1/2 Portada ya enviada. "
                "No se volverá a publicar."
            )

            print(
                f"  message_id existente: "
                f"{portada_message_id}"
            )

        else:

            print(
                "1/2 Enviando portada + caption..."
            )

            respuesta_portada = (
                enviar_portada(
                    token,
                    chat_id,
                    mensaje_1
                )
            )

            mensaje_portada = (
                respuesta_portada.get(
                    "result",
                    {}
                )
            )

            portada_message_id = (
                mensaje_portada.get(
                    "message_id"
                )
            )

            if portada_message_id is None:
                raise RuntimeError(
                    "Telegram no devolvió "
                    "message_id para la portada."
                )

            print(
                "✓ Mensaje de portada enviado."
            )

            print(
                f"  message_id: "
                f"{portada_message_id}"
            )

            # -------------------------------------------------
            # GUARDAR INMEDIATAMENTE
            # -------------------------------------------------

            if (
                pista is not None
                and state_file is not None
            ):

                registrar_portada_enviada(
                    pista,
                    portada_message_id
                )

                guardar_estado_actual(
                    estado,
                    state_file,
                    release
                )

                print(
                    "✓ Estado de portada guardado "
                    "inmediatamente."
                )

        # =====================================================
        # PREVIEW
        # =====================================================

        preview_message_id = None
        preview_url = None
        preview_fuente = None
        preview_duration = None

        if (
            pista is not None
            and preview_enviada(pista)
        ):

            preview_message_id = (
                pista["preview"]["message_id"]
            )

            print("")
            print(
                "2/2 Preview ya enviada. "
                "No se volverá a publicar."
            )

            print(
                f"  message_id existente: "
                f"{preview_message_id}"
            )

        else:

            preview_url = (
                obtener_preview_url(
                    mensaje_2
                )
            )

            preview_fuente = (
                obtener_fuente_preview(
                    mensaje_2
                )
            )

            print("")
            print(
                "Preview detectado:"
            )

            print(
                f"  URL: {preview_url}"
            )

            if preview_fuente:
                print(
                    f"  Fuente: {preview_fuente}"
                )

            preview_path = (
                descargar_preview(
                    preview_url
                )
            )

            # =================================================
            # DURACIÓN REAL
            # =================================================

            print("")
            print(
                "Detectando duración real "
                "del preview..."
            )

            preview_duration = (
                obtener_duracion_archivo(
                    preview_path
                )
            )

            duracion_cancion = (
                mensaje_2.get(
                    "duracion_segundos"
                )
            )

            print(
                "✓ Duración real del preview:"
            )

            print(
                f"  {preview_duration} segundos"
            )

            if duracion_cancion is not None:
                print(
                    "  Duración completa de la "
                    f"canción: {duracion_cancion} segundos"
                )

            # =================================================
            # MENSAJE 2
            # =================================================

            print("")
            print(
                "2/2 Enviando preview + botón..."
            )

            respuesta_preview = (
                enviar_preview(
                    token,
                    chat_id,
                    mensaje_2,
                    preview_path,
                    preview_duration
                )
            )

            mensaje_preview = (
                respuesta_preview.get(
                    "result",
                    {}
                )
            )

            preview_message_id = (
                mensaje_preview.get(
                    "message_id"
                )
            )

            if preview_message_id is None:
                raise RuntimeError(
                    "Telegram no devolvió "
                    "message_id para el preview."
                )

            print(
                "✓ Mensaje de preview enviado."
            )

            print(
                f"  message_id: "
                f"{preview_message_id}"
            )

            # -------------------------------------------------
            # GUARDAR INMEDIATAMENTE
            # -------------------------------------------------

            if (
                pista is not None
                and state_file is not None
            ):

                registrar_preview_enviada(
                    pista,
                    preview_message_id
                )

                guardar_estado_actual(
                    estado,
                    state_file,
                    release
                )

                print(
                    "✓ Estado de preview guardado "
                    "inmediatamente."
                )

        # =====================================================
        # ESTADO FINAL DE LA PISTA
        # =====================================================

        if (
            pista is not None
            and state_file is not None
        ):

            guardar_estado_actual(
                estado,
                state_file,
                release
            )

            print("")
            print(
                "Estado final de la pista:"
            )

            print(
                f"  {pista.get('estado')}"
            )

            print(
                f"  Portada: "
                f"{pista['portada']['message_id']}"
            )

            print(
                f"  Preview: "
                f"{pista['preview']['message_id']}"
            )

            print(
                f"Estado del release: "
                f"{release.get('estado')}"
            )

        # =====================================================
        # DATOS DEL RESULTADO
        # =====================================================

        duracion_cancion = (
            mensaje_2.get(
                "duracion_segundos"
            )
        )

        boton = obtener_boton(
            mensaje_2
        )

        resultado_final = {
            "ok": True,
            "chat_id": chat_id,
            "mensaje_portada": {
                "message_id":
                    portada_message_id
            },
            "mensaje_preview": {
                "message_id":
                    preview_message_id
            },
            "preview_fuente":
                preview_fuente,
            "preview_duracion_segundos":
                preview_duration,
            "duracion_cancion_segundos":
                duracion_cancion,
            "boton": boton
        }

        # -----------------------------------------------------
        # Información de estado
        # -----------------------------------------------------

        if (
            pista is not None
            and release is not None
        ):

            resultado_final["estado"] = {
                "deezer_album_id":
                    release.get(
                        "deezer_album_id"
                    ),
                "deezer_track_id":
                    pista.get(
                        "deezer_track_id"
                    ),
                "track_index":
                    pista.get(
                        "index"
                    ),
                "pista":
                    pista.get(
                        "estado"
                    ),
                "release":
                    release.get(
                        "estado"
                    )
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
            "PUBLICACIÓN EN TELEGRAM EXITOSA"
        )

    except Exception as e:

        print(
            f"ERROR: {e}"
        )

        sys.exit(1)

    finally:

        if (
            preview_path
            and preview_path.exists()
        ):

            try:
                preview_path.unlink()

            except Exception:
                pass


if __name__ == "__main__":
    main()
