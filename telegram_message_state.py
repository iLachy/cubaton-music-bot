"""Estado granular y seguro de los mensajes publicados en Telegram.

Cada canción tiene dos pasos independientes: cover y preview. Un envío que
queda en "sending" tras una interrupción pasa a "unknown": no se reenvía
automáticamente porque Telegram pudo haberlo aceptado y perdido la respuesta.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_VERSION = 1
DEFAULT_STATE_FILE = Path("state/telegram_messages.json")
STEP_NAMES = ("cover", "preview")


class PublicationStateError(RuntimeError):
    """El estado no se puede cargar o actualizar de forma segura."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_step() -> dict[str, Any]:
    return {
        "status": "pending",
        "message_id": None,
        "started_at": None,
        "sent_at": None,
        "error": None,
    }


class TelegramMessageState:
    """Gestiona el estado individual de portada y preview por canción."""

    def __init__(self, path: str | Path = DEFAULT_STATE_FILE):
        self.path = Path(path)
        self.data: dict[str, Any] = {
            "version": STATE_VERSION,
            "songs": {},
            "updated_at": _now(),
        }
        self._load()
        self._recover_interrupted_sends()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except Exception as error:
            raise PublicationStateError(
                f"No se pudo leer {self.path}: {error}. "
                "Se detiene el bot para evitar publicaciones duplicadas."
            ) from error
        if not isinstance(loaded, dict):
            raise PublicationStateError("El estado de Telegram no es un objeto JSON.")
        if loaded.get("version") != STATE_VERSION:
            raise PublicationStateError(
                f"Versión incompatible en {self.path}: {loaded.get('version')!r}; "
                f"se esperaba {STATE_VERSION}. No se reconstruirá automáticamente."
            )
        if not isinstance(loaded.get("songs"), dict):
            raise PublicationStateError("El campo 'songs' debe ser un objeto JSON.")
        self.data = loaded

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["updated_at"] = _now()
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=str(self.path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
            try:
                dir_fd = os.open(str(self.path.parent), os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except (AttributeError, OSError):
                pass
        except Exception as error:
            try:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
            except OSError:
                pass
            raise PublicationStateError(
                f"No se pudo guardar el estado {self.path}: {error}"
            ) from error

    def _recover_interrupted_sends(self) -> None:
        changed = False
        for song in self.data["songs"].values():
            if not isinstance(song, dict):
                continue
            for name in STEP_NAMES:
                step = song.get(name)
                if isinstance(step, dict) and step.get("status") == "sending":
                    step["status"] = "unknown"
                    step["error"] = (
                        "Interrupción durante el envío: Telegram pudo haber "
                        "recibido el mensaje. Revisión manual requerida."
                    )
                    changed = True
        if changed:
            self._save()

    def ensure_song(
        self,
        song_key: str,
        *,
        song_id: str | None = None,
        title: str | None = None,
        artists: str | None = None,
        video_id: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(song_key, str) or not song_key.strip():
            raise ValueError("song_key debe ser una cadena no vacía.")
        song = self.data["songs"].get(song_key)
        if song is None:
            song = {
                "song_id": song_id,
                "title": title,
                "artists": artists,
                "video_id": video_id,
                "cover": _new_step(),
                "preview": _new_step(),
                "created_at": _now(),
                "updated_at": _now(),
            }
            self.data["songs"][song_key] = song
        else:
            if not isinstance(song, dict):
                raise PublicationStateError(f"Registro inválido: {song_key}")
            song.setdefault("cover", _new_step())
            song.setdefault("preview", _new_step())
            song["song_id"] = song_id or song.get("song_id")
            song["title"] = title or song.get("title")
            song["artists"] = artists or song.get("artists")
            song["video_id"] = video_id or song.get("video_id")
            song["updated_at"] = _now()
        self._save()
        return song

    def get_song(self, song_key: str) -> dict[str, Any] | None:
        return self.data["songs"].get(song_key)

    def get_step(self, song_key: str, step_name: str) -> dict[str, Any]:
        if step_name not in STEP_NAMES:
            raise ValueError(f"Paso inválido: {step_name}")
        song = self.data["songs"].get(song_key)
        if not isinstance(song, dict):
            raise PublicationStateError(f"No existe la canción: {song_key}")
        step = song.get(step_name)
        if not isinstance(step, dict):
            raise PublicationStateError(f"Estado inválido para {song_key}/{step_name}")
        return step

    def mark_sending(self, song_key: str, step_name: str) -> None:
        step = self.get_step(song_key, step_name)
        if step["status"] == "sent":
            return
        if step["status"] == "unknown":
            raise PublicationStateError(
                f"Envío {step_name} de {song_key} en estado unknown; "
                "requiere revisión manual."
            )
        step.update(status="sending", started_at=_now(), error=None)
        self.data["songs"][song_key]["updated_at"] = _now()
        self._save()

    def mark_sent(self, song_key: str, step_name: str, message_id: int) -> None:
        if not isinstance(message_id, int) or message_id <= 0:
            raise ValueError("message_id debe ser un entero positivo.")
        step = self.get_step(song_key, step_name)
        step.update(status="sent", message_id=message_id, sent_at=_now(), error=None)
        self.data["songs"][song_key]["updated_at"] = _now()
        self._save()

    def mark_failed(self, song_key: str, step_name: str, error: str) -> None:
        step = self.get_step(song_key, step_name)
        step.update(status="failed", error=str(error)[:2000])
        self.data["songs"][song_key]["updated_at"] = _now()
        self._save()

    def mark_unknown(self, song_key: str, step_name: str, error: str) -> None:
        step = self.get_step(song_key, step_name)
        step.update(status="unknown", error=str(error)[:2000])
        self.data["songs"][song_key]["updated_at"] = _now()
        self._save()

    def mark_not_available(self, song_key: str, step_name: str, reason: str) -> None:
        if step_name != "preview":
            raise ValueError("Solo el preview puede marcarse como no disponible.")
        step = self.get_step(song_key, step_name)
        step.update(
            status="not_available",
            message_id=None,
            sent_at=None,
            error=str(reason)[:2000],
        )
        self.data["songs"][song_key]["updated_at"] = _now()
        self._save()

    def is_step_complete(self, song_key: str, step_name: str) -> bool:
        status = self.get_step(song_key, step_name)["status"]
        return status == "sent" or (step_name == "preview" and status == "not_available")

    def is_song_complete(self, song_key: str) -> bool:
        return all(self.is_step_complete(song_key, name) for name in STEP_NAMES)

    def pending_steps(self, song_key: str) -> list[str]:
        return [
            name for name in STEP_NAMES
            if self.get_step(song_key, name)["status"] in ("pending", "failed")
        ]
