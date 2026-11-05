"""
Configuración centralizada de logging para Cubaton Music Bot.

Uso típico al inicio de un script:

    from logging_setup import get_logger
    log = get_logger(__name__)

    log.info("Bot iniciado")
    log.warning("Sin portada para %s", titulo)
    log.error("Fallo al publicar: %s", error)

En GitHub Actions los logs aparecen en la salida del job.
En local también se escriben por consola.
"""

from __future__ import annotations

import logging
import os
import sys


_CONFIGURED = False


def setup_logging(level: str | None = None) -> None:
    """
    Configura el logging una sola vez.

    level: DEBUG, INFO, WARNING, ERROR (por defecto INFO).
    Se puede sobreescribir con la variable de entorno LOG_LEVEL.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = (
        level
        or os.environ.get("LOG_LEVEL", "INFO")
    ).upper()

    numeric_level = getattr(
        logging,
        level_name,
        logging.INFO,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(numeric_level)

    # Reducir ruido de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str = "cubaton") -> logging.Logger:
    """
    Devuelve un logger listo para usar.

    Llama a setup_logging() la primera vez.
    """
    setup_logging()
    return logging.getLogger(name)
