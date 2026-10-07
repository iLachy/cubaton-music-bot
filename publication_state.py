#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
publication_state.py

Gestor de estado persistente para las publicaciones de Telegram.

Responsabilidades:
- Crear/cargar data/publication_state.json
- Registrar releases por Deezer album ID
- Registrar tracks por Deezer track ID
- Registrar individualmente:
    - mensaje de portada
    - mensaje de preview/audio
- Detectar pistas completamente publicadas
- Detectar pistas parcialmente publicadas
- Permitir reanudar una publicación sin duplicar mensajes ya enviados
- Mantener el estado en un JSON sencillo y legible

Este archivo NO envía mensajes a Telegram.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# ============================================================
# CONFIGURACIÓN
# ============================================================

DEFAULT_STATE_FILE = Path("data/publication_state.json")

STATE_VERSION = 1


# ============================================================
# UTILIDADES
# ============================================================

def ahora_utc() -> str:
    """
    Devuelve la fecha/hora actual en UTC en formato ISO 8601.
    """
    return datetime.now(timezone.utc).isoformat()


def convertir_id(valor: Any) -> Optional[str]:
    """
    Convierte un ID a string de forma segura.

    Los IDs de Deezer normalmente llegan como enteros,
    pero los guardamos como strings para evitar problemas
    al utilizarlos como claves JSON.
    """
    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    return texto


def asegurar_directorio(path: Path) -> None:
    """
    Crea el directorio padre del archivo de estado si no existe.
    """
    path.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# ESTRUCTURA VACÍA
# ============================================================

def estado_vacio() -> Dict[str, Any]:
    """
    Devuelve la estructura inicial del archivo de estado.
    """
    return {
        "version": STATE_VERSION,
        "updated_at": ahora_utc(),
        "releases": {}
    }


# ============================================================
# CARGA / GUARDADO
# ============================================================

def cargar_estado(
    state_file: Path | str = DEFAULT_STATE_FILE
) -> Dict[str, Any]:
    """
    Carga el estado persistente.

    Si el archivo no existe:
        - crea la estructura inicial
        - la guarda
        - la devuelve

    Si existe pero está vacío:
        - devuelve estructura inicial

    Si existe pero contiene JSON inválido:
        - lanza ValueError
    """

    path = Path(state_file)

    if not path.exists():
        estado = estado_vacio()
        guardar_estado(estado, path)
        return estado

    try:
        with path.open("r", encoding="utf-8") as f:
            contenido = f.read().strip()

    except OSError as exc:
        raise RuntimeError(
            f"No se pudo leer el archivo de estado: {path}"
        ) from exc

    if not contenido:
        estado = estado_vacio()
        guardar_estado(estado, path)
        return estado

    try:
        estado = json.loads(contenido)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"El archivo de estado contiene JSON inválido: {path}"
        ) from exc

    if not isinstance(estado, dict):
        raise ValueError(
            "El archivo de estado debe contener un objeto JSON."
        )

    # --------------------------------------------------------
    # Compatibilidad defensiva
    # --------------------------------------------------------

    if "version" not in estado:
        estado["version"] = STATE_VERSION

    if "releases" not in estado:
        estado["releases"] = {}

    if not isinstance(estado["releases"], dict):
        raise ValueError(
            "El campo 'releases' debe ser un objeto JSON."
        )

    if "updated_at" not in estado:
        estado["updated_at"] = ahora_utc()

    return estado


def guardar_estado(
    estado: Dict[str, Any],
    state_file: Path | str = DEFAULT_STATE_FILE
) -> None:
    """
    Guarda el estado de forma atómica.

    En lugar de escribir directamente sobre publication_state.json,
    primero escribe un archivo temporal y luego lo reemplaza.

    Esto reduce el riesgo de dejar un JSON corrupto si el proceso
    termina durante la escritura.
    """

    path = Path(state_file)

    asegurar_directorio(path)

    estado["version"] = STATE_VERSION
    estado["updated_at"] = ahora_utc()

    contenido = json.dumps(
        estado,
        ensure_ascii=False,
        indent=2
    )

    temp_path: Optional[Path] = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False
        ) as temp_file:

            temp_file.write(contenido)
            temp_file.flush()
            os.fsync(temp_file.fileno())

            temp_path = Path(temp_file.name)

        os.replace(temp_path, path)

    except OSError as exc:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

        raise RuntimeError(
            f"No se pudo guardar el archivo de estado: {path}"
        ) from exc


# ============================================================
# RELEASES
# ============================================================

def obtener_release(
    estado: Dict[str, Any],
    deezer_album_id: Any
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un release por Deezer album ID.

    Devuelve None si todavía no existe.
    """

    album_id = convertir_id(deezer_album_id)

    if album_id is None:
        return None

    return estado.get("releases", {}).get(album_id)


def crear_o_actualizar_release(
    estado: Dict[str, Any],
    *,
    deezer_album_id: Any,
    deezer_url: Optional[str] = None,
    tipo: Optional[str] = None,
    nombre_publicacion: Optional[str] = None,
    fecha: Optional[str] = None,
    portada: Optional[str] = None,
    total_pistas: Optional[int] = None
) -> Dict[str, Any]:
    """
    Crea un release si no existe o actualiza sus datos generales
    si ya existe.

    No modifica el estado individual de las pistas.
    """

    album_id = convertir_id(deezer_album_id)

    if album_id is None:
        raise ValueError(
            "deezer_album_id es obligatorio para crear un release."
        )

    releases = estado.setdefault("releases", {})

    ahora = ahora_utc()

    release = releases.get(album_id)

    if release is None:
        release = {
            "deezer_album_id": album_id,
            "deezer_url": deezer_url,
            "tipo": tipo,
            "nombre_publicacion": nombre_publicacion,
            "fecha": fecha,
            "portada": portada,
            "total_pistas": total_pistas,
            "estado": "pending",
            "created_at": ahora,
            "updated_at": ahora,
            "pistas": {}
        }

        releases[album_id] = release

    else:
        # --------------------------------------------------------
        # Actualizar únicamente los datos disponibles.
        # --------------------------------------------------------

        if deezer_url is not None:
            release["deezer_url"] = deezer_url

        if tipo is not None:
            release["tipo"] = tipo

        if nombre_publicacion is not None:
            release["nombre_publicacion"] = nombre_publicacion

        if fecha is not None:
            release["fecha"] = fecha

        if portada is not None:
            release["portada"] = portada

        if total_pistas is not None:
            release["total_pistas"] = total_pistas

        release["updated_at"] = ahora

        if "pistas" not in release:
            release["pistas"] = {}

    return release


# ============================================================
# TRACKS
# ============================================================

def obtener_pista(
    release: Dict[str, Any],
    deezer_track_id: Any
) -> Optional[Dict[str, Any]]:
    """
    Obtiene una pista por Deezer track ID.
    """

    track_id = convertir_id(deezer_track_id)

    if track_id is None:
        return None

    pistas = release.setdefault("pistas", {})

    return pistas.get(track_id)


def crear_o_actualizar_pista(
    release: Dict[str, Any],
    *,
    deezer_track_id: Any,
    index: Optional[int] = None,
    titulo: Optional[str] = None,
    titulo_publicacion: Optional[str] = None,
    artistas: Any = None,
    duracion_segundos: Optional[int] = None,
    isrc: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una pista si no existe o actualiza sus metadatos.

    No modifica los estados de portada ni preview.
    """

    track_id = convertir_id(deezer_track_id)

    if track_id is None:
        raise ValueError(
            "deezer_track_id es obligatorio para crear una pista."
        )

    pistas = release.setdefault("pistas", {})

    ahora = ahora_utc()

    pista = pistas.get(track_id)

    if pista is None:
        pista = {
            "deezer_track_id": track_id,
            "index": index,
            "titulo": titulo,
            "titulo_publicacion": titulo_publicacion,
            "artistas": artistas,
            "duracion_segundos": duracion_segundos,
            "isrc": isrc,
            "estado": "pending",
            "created_at": ahora,
            "updated_at": ahora,
            "portada": {
                "enviada": False,
                "message_id": None
            },
            "preview": {
                "enviada": False,
                "message_id": None
            }
        }

        pistas[track_id] = pista

    else:
        if index is not None:
            pista["index"] = index

        if titulo is not None:
            pista["titulo"] = titulo

        if titulo_publicacion is not None:
            pista["titulo_publicacion"] = titulo_publicacion

        if artistas is not None:
            pista["artistas"] = artistas

        if duracion_segundos is not None:
            pista["duracion_segundos"] = duracion_segundos

        if isrc is not None:
            pista["isrc"] = isrc

        if "portada" not in pista:
            pista["portada"] = {
                "enviada": False,
                "message_id": None
            }

        if "preview" not in pista:
            pista["preview"] = {
                "enviada": False,
                "message_id": None
            }

        if "estado" not in pista:
            pista["estado"] = "pending"

        pista["updated_at"] = ahora

    return pista


# ============================================================
# MENSAJE DE PORTADA
# ============================================================

def registrar_portada_enviada(
    pista: Dict[str, Any],
    message_id: Any
) -> Dict[str, Any]:
    """
    Marca el mensaje de portada como enviado y guarda su message_id.
    """

    if message_id is None:
        raise ValueError(
            "message_id es obligatorio para registrar la portada."
        )

    try:
        message_id_normalizado = int(message_id)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "message_id de portada debe ser un entero."
        ) from exc

    pista["portada"] = {
        "enviada": True,
        "message_id": message_id_normalizado
    }

    actualizar_estado_pista(pista)

    return pista


# ============================================================
# MENSAJE DE PREVIEW
# ============================================================

def registrar_preview_enviada(
    pista: Dict[str, Any],
    message_id: Any
) -> Dict[str, Any]:
    """
    Marca el mensaje de preview/audio como enviado y guarda
    su message_id.
    """

    if message_id is None:
        raise ValueError(
            "message_id es obligatorio para registrar la preview."
        )

    try:
        message_id_normalizado = int(message_id)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "message_id de preview debe ser un entero."
        ) from exc

    pista["preview"] = {
        "enviada": True,
        "message_id": message_id_normalizado
    }

    actualizar_estado_pista(pista)

    return pista


# ============================================================
# ESTADO DE PISTA
# ============================================================

def portada_enviada(pista: Dict[str, Any]) -> bool:
    """
    Devuelve True si la portada ya fue enviada.
    """

    portada = pista.get("portada")

    if not isinstance(portada, dict):
        return False

    return (
        portada.get("enviada") is True
        and portada.get("message_id") is not None
    )


def preview_enviada(pista: Dict[str, Any]) -> bool:
    """
    Devuelve True si la preview/audio ya fue enviada.
    """

    preview = pista.get("preview")

    if not isinstance(preview, dict):
        return False

    return (
        preview.get("enviada") is True
        and preview.get("message_id") is not None
    )


def pista_completada(pista: Dict[str, Any]) -> bool:
    """
    Una pista está completa únicamente cuando sus dos mensajes
    fueron enviados correctamente.
    """

    return portada_enviada(pista) and preview_enviada(pista)


def actualizar_estado_pista(
    pista: Dict[str, Any]
) -> str:
    """
    Actualiza automáticamente el estado de la pista.

    Estados posibles:
        pending
        partial
        completed
    """

    portada = portada_enviada(pista)
    preview = preview_enviada(pista)

    if portada and preview:
        estado = "completed"
    elif portada or preview:
        estado = "partial"
    else:
        estado = "pending"

    pista["estado"] = estado
    pista["updated_at"] = ahora_utc()

    return estado


# ============================================================
# ESTADO DEL RELEASE
# ============================================================

def actualizar_estado_release(
    release: Dict[str, Any]
) -> str:
    """
    Actualiza el estado general del release basándose en sus pistas.

    Estados posibles:
        pending
        partial
        completed
    """

    pistas = release.get("pistas", {})

    if not pistas:
        release["estado"] = "pending"
        release["updated_at"] = ahora_utc()
        return "pending"

    estados = []

    for pista in pistas.values():
        estados.append(actualizar_estado_pista(pista))

    if all(estado == "completed" for estado in estados):
        estado_release = "completed"

    elif any(
        estado in ("partial", "completed")
        for estado in estados
    ):
        estado_release = "partial"

    else:
        estado_release = "pending"

    release["estado"] = estado_release
    release["updated_at"] = ahora_utc()

    return estado_release


# ============================================================
# RESUMEN
# ============================================================

def resumen_release(
    release: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Devuelve un resumen del estado de un release.
    """

    pistas = release.get("pistas", {})

    total = len(pistas)
    completadas = 0
    parciales = 0
    pendientes = 0

    for pista in pistas.values():
        estado = actualizar_estado_pista(pista)

        if estado == "completed":
            completadas += 1

        elif estado == "partial":
            parciales += 1

        else:
            pendientes += 1

    estado_release = actualizar_estado_release(release)

    return {
        "deezer_album_id": release.get("deezer_album_id"),
        "nombre_publicacion": release.get("nombre_publicacion"),
        "estado": estado_release,
        "total_pistas": total,
        "pistas_completadas": completadas,
        "pistas_parciales": parciales,
        "pistas_pendientes": pendientes
    }


# ============================================================
# BÚSQUEDA DE PISTAS PENDIENTES
# ============================================================

def obtener_pistas_pendientes(
    release: Dict[str, Any]
) -> list[Dict[str, Any]]:
    """
    Devuelve las pistas que todavía necesitan algún mensaje.

    Se conserva el orden original mediante el campo 'index'.
    """

    pistas = release.get("pistas", {})

    pendientes = []

    for pista in pistas.values():
        actualizar_estado_pista(pista)

        if pista.get("estado") != "completed":
            pendientes.append(pista)

    pendientes.sort(
        key=lambda pista: (
            pista.get("index")
            if isinstance(pista.get("index"), int)
            else 999999
        )
    )

    return pendientes


# ============================================================
# VALIDACIÓN
# ============================================================

def validar_estado(
    estado: Dict[str, Any]
) -> None:
    """
    Realiza una validación estructural del estado.

    Lanza ValueError si encuentra una inconsistencia grave.
    """

    if not isinstance(estado, dict):
        raise ValueError(
            "El estado debe ser un objeto."
        )

    if not isinstance(
        estado.get("releases"),
        dict
    ):
        raise ValueError(
            "El estado debe contener 'releases' como objeto."
        )

    for album_id, release in estado["releases"].items():

        if not isinstance(release, dict):
            raise ValueError(
                f"Release inválido: {album_id}"
            )

        if str(release.get("deezer_album_id")) != str(album_id):
            raise ValueError(
                "El deezer_album_id del release no coincide "
                f"con su clave: {album_id}"
            )

        pistas = release.get("pistas")

        if not isinstance(pistas, dict):
            raise ValueError(
                f"Las pistas del release {album_id} "
                "deben ser un objeto."
            )

        for track_id, pista in pistas.items():

            if not isinstance(pista, dict):
                raise ValueError(
                    f"Pista inválida: {track_id}"
                )

            if str(
                pista.get("deezer_track_id")
            ) != str(track_id):
                raise ValueError(
                    "El deezer_track_id de la pista no coincide "
                    f"con su clave: {track_id}"
                )

            portada = pista.get("portada")

            if not isinstance(portada, dict):
                raise ValueError(
                    f"La portada de la pista {track_id} "
                    "debe ser un objeto."
                )

            preview = pista.get("preview")

            if not isinstance(preview, dict):
                raise ValueError(
                    f"La preview de la pista {track_id} "
                    "debe ser un objeto."
                )


# ============================================================
# CLI DE PRUEBA
# ============================================================

def ejecutar_prueba(
    state_file: Path | str = DEFAULT_STATE_FILE
) -> None:
    """
    Prueba local completa de la capa de estado.

    No utiliza Telegram.
    """

    print("==========================================")
    print("TEST publication_state.py")
    print("==========================================")
    print("")

    path = Path(state_file)

    # --------------------------------------------------------
    # Para la prueba utilizamos un archivo temporal separado.
    # --------------------------------------------------------

    if path.exists():
        path.unlink()

    print("1. Cargando estado inicial...")

    estado = cargar_estado(path)

    validar_estado(estado)

    print("✓ Estado inicial válido")
    print("")

    # --------------------------------------------------------
    # Crear release
    # --------------------------------------------------------

    print("2. Creando release...")

    release = crear_o_actualizar_release(
        estado,
        deezer_album_id=917540341,
        deezer_url="https://www.deezer.com/mx/album/917540341",
        tipo="EP",
        nombre_publicacion="LBMA",
        fecha="13-02-2026",
        portada=(
            "https://cdn-images.dzcdn.net/images/cover/"
            "5a00c1412a939d7e5e953fedcf14f2b1/"
            "1000x1000-000000-80-0-0.jpg"
        ),
        total_pistas=4
    )

    print("✓ Release creado")
    print("  ID:", release["deezer_album_id"])
    print("  Nombre:", release["nombre_publicacion"])
    print("")

    # --------------------------------------------------------
    # Crear 4 pistas
    # --------------------------------------------------------

    print("3. Creando 4 pistas...")

    tracks = [
        (
            3839609781,
            1,
            "Te Amaré",
            "Te Amaré (Prod. by El Bandolero x Roberto Ferrante)"
        ),
        (
            3839609782,
            2,
            "Quizás",
            "Quizás (Prod. by Roberto Ferrante x El Bandolero)"
        ),
        (
            3839609783,
            3,
            "Machuka",
            "Machuka (Prod. by Dj Honda)"
        ),
        (
            3839609784,
            4,
            "Se Va",
            "Se Va (Prod. by Dj Honda)"
        )
    ]

    for (
        track_id,
        index,
        titulo,
        titulo_publicacion
    ) in tracks:

        crear_o_actualizar_pista(
            release,
            deezer_track_id=track_id,
            index=index,
            titulo=titulo,
            titulo_publicacion=titulo_publicacion
        )

    print("✓ 4 pistas creadas")
    print("")

    # --------------------------------------------------------
    # Guardar
    # --------------------------------------------------------

    print("4. Guardando estado...")

    guardar_estado(estado, path)

    print("✓ Estado guardado")
    print("")

    # --------------------------------------------------------
    # Simular publicación parcial
    # --------------------------------------------------------

    print("5. Simulando publicación parcial...")

    pista_1 = obtener_pista(
        release,
        3839609781
    )

    pista_2 = obtener_pista(
        release,
        3839609782
    )

    pista_3 = obtener_pista(
        release,
        3839609783
    )

    pista_4 = obtener_pista(
        release,
        3839609784
    )

    if not pista_1 or not pista_2 or not pista_3 or not pista_4:
        raise RuntimeError(
            "No se pudieron recuperar las 4 pistas."
        )

    # Pista 1: completamente publicada.
    registrar_portada_enviada(
        pista_1,
        581
    )

    registrar_preview_enviada(
        pista_1,
        582
    )

    # Pista 2: completamente publicada.
    registrar_portada_enviada(
        pista_2,
        583
    )

    registrar_preview_enviada(
        pista_2,
        584
    )

    # Pista 3: solamente portada.
    registrar_portada_enviada(
        pista_3,
        585
    )

    # Pista 4: todavía pendiente.

    actualizar_estado_release(release)

    guardar_estado(estado, path)

    print("✓ Estado parcial creado")
    print("")

    # --------------------------------------------------------
    # Comprobar estados
    # --------------------------------------------------------

    print("6. Comprobando estados...")

    assert pista_1["estado"] == "completed"
    assert pista_2["estado"] == "completed"
    assert pista_3["estado"] == "partial"
    assert pista_4["estado"] == "pending"

    print("✓ Pista 1: completed")
    print("✓ Pista 2: completed")
    print("✓ Pista 3: partial")
    print("✓ Pista 4: pending")
    print("")

    # --------------------------------------------------------
    # Comprobar IDs
    # --------------------------------------------------------

    print("7. Comprobando message_id...")

    assert pista_1["portada"]["message_id"] == 581
    assert pista_1["preview"]["message_id"] == 582

    assert pista_2["portada"]["message_id"] == 583
    assert pista_2["preview"]["message_id"] == 584

    assert pista_3["portada"]["message_id"] == 585
    assert pista_3["preview"]["message_id"] is None

    print("✓ IDs de mensajes conservados correctamente")
    print("")

    # --------------------------------------------------------
    # Comprobar pendientes
    # --------------------------------------------------------

    print("8. Detectando pistas pendientes...")

    pendientes = obtener_pistas_pendientes(
        release
    )

    indices = [
        pista["index"]
        for pista in pendientes
    ]

    assert indices == [3, 4]

    print(
        "✓ Pistas pendientes/parciales:",
        indices
    )
    print("")

    # --------------------------------------------------------
    # Resumen
    # --------------------------------------------------------

    print("9. Resumen del release...")

    resumen = resumen_release(release)

    print(
        json.dumps(
            resumen,
            ensure_ascii=False,
            indent=2
        )
    )

    assert resumen["estado"] == "partial"
    assert resumen["total_pistas"] == 4
    assert resumen["pistas_completadas"] == 2
    assert resumen["pistas_parciales"] == 1
    assert resumen["pistas_pendientes"] == 1

    print("")
    print("✓ Resumen correcto")

    # --------------------------------------------------------
    # Recargar desde disco
    # --------------------------------------------------------

    print("")
    print("10. Recargando estado desde disco...")

    estado_recargado = cargar_estado(path)

    validar_estado(estado_recargado)

    release_recargado = obtener_release(
        estado_recargado,
        917540341
    )

    if release_recargado is None:
        raise RuntimeError(
            "El release no apareció después de recargar."
        )

    pista_3_recargada = obtener_pista(
        release_recargado,
        3839609783
    )

    if pista_3_recargada is None:
        raise RuntimeError(
            "La pista 3 no apareció después de recargar."
        )

    assert pista_3_recargada["estado"] == "partial"
    assert (
        pista_3_recargada["portada"]["message_id"]
        == 585
    )
    assert (
        pista_3_recargada["preview"]["message_id"]
        is None
    )

    print("✓ Estado persistió correctamente")
    print("")

    # --------------------------------------------------------
    # Mostrar JSON final
    # --------------------------------------------------------

    print("11. Estado persistente generado:")
    print("")

    with path.open("r", encoding="utf-8") as f:
        print(f.read())

    print("")
    print("==========================================")
    print("✓ TEST COMPLETADO CORRECTAMENTE")
    print("==========================================")

    # --------------------------------------------------------
    # Limpiar archivo temporal de prueba.
    # --------------------------------------------------------

    try:
        path.unlink()
    except OSError:
        pass


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    ejecutar_prueba()
