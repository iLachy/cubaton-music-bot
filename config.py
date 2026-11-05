"""
Configuración del Cubaton Music Bot.

Toda la configuración centralizada vive aquí para que sea fácil
de ajustar sin tocar la lógica principal del bot.
"""

import os

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Canal principal donde se publican los lanzamientos
TELEGRAM_CHAT_ID = "@Cubaton_Music"

# Chat donde se envían alertas de errores (opcional)
TELEGRAM_ALERT_CHAT_ID = (
    os.environ.get("TELEGRAM_ALERT_CHAT_ID")
    or os.environ.get("TELEGRAM_CHAT_ID")
)

TELEGRAM_API = (
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    if TELEGRAM_BOT_TOKEN
    else None
)

# ---------------------------------------------------------------------------
# Filtros de publicación
# ---------------------------------------------------------------------------

# No se publican canciones cuyo año sea anterior al año actual menos este
# valor (1 = solo año actual y anterior). Las descartadas se registran como
# históricas. Para pruebas con canciones antiguas, súbelo temporalmente.
MAX_ANTIGUEDAD_ANIOS = 1

# Si no se logra resolver el álbum para obtener la portada, publicar la
# canción solo con texto y botón (True) en lugar de reintentar y enviar
# una alerta en cada ejecución (False).
PUBLICAR_SIN_PORTADA_SI_FALLA = True

# Envía debajo de cada publicación un adelanto de unos 30 segundos
# (preview oficial para promoción: Apple Music y, como respaldo, Deezer).
# Si no se encuentra la canción o falla el envío, simplemente no se envía
# y no se genera alerta.
ENVIAR_PREVIEW_AUDIO = True

# Botón "Escuchar en YouTube Music" en el post principal.
# Con False solo aparece en el post cuando no hay preview de audio;
# el preview lo lleva siempre.
BOTON_EN_POST = False

# Pausa (segundos) tras cada pareja Post + Audio, para no superar los
# límites de envío de Telegram al publicar varias canciones seguidas.
PAUSA_ENTRE_PUBLICACIONES = 2

# ---------------------------------------------------------------------------
# Fuentes de detección
# ---------------------------------------------------------------------------

# Busca canciones donde participa un artista monitorizado pero que están en
# el canal de otro artista (colaboraciones). Solo se consideran las del año
# actual; las de años anteriores se registran como históricas.
# La primera vez que se busca para cada artista, todo lo encontrado se
# registra sin publicar.
BUSCAR_COLABORACIONES = False

# Detecta lanzamientos nuevos también en Deezer (suelen llegar antes que a
# YouTube Music). Requiere "deezer_id" en cada artista.
# La primera vez que se lee cada artista, todo lo existente se registra
# sin publicar.
BUSCAR_EN_DEEZER = False

DEEZER_API = "https://api.deezer.com"

# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

STATE_FILE = "state/releases.json"
