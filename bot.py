import os
import re
import time
import json
import html
import unicodedata
from datetime import datetime, timezone
from io import BytesIO

import requests
from PIL import Image
from ytmusicapi import YTMusic

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_ALERT_CHAT_ID,
    TELEGRAM_API,
    MAX_ANTIGUEDAD_ANIOS,
    PUBLICAR_SIN_PORTADA_SI_FALLA,
    ENVIAR_PREVIEW_AUDIO,
    BOTON_EN_POST,
    PAUSA_ENTRE_PUBLICACIONES,
    BUSCAR_COLABORACIONES,
    BUSCAR_EN_DEEZER,
    DEEZER_API,
    STATE_FILE,
)
from artists import ARTISTAS


# ============================================================
# UTILIDADES
# ============================================================

def escapar(texto):
    """Escapa texto para Telegram HTML."""
    if texto is None:
        return ""

    return html.escape(str(texto))
