# Cubaton Music Bot

Bot de Telegram que monitoriza lanzamientos de música urbana cubana y los publica automáticamente en [@Cubaton_Music](https://t.me/Cubaton_Music).

Detecta canciones nuevas en **YouTube Music** (y opcionalmente **Deezer**), obtiene portadas y previews (Apple Music / Deezer) y publica en el canal con un formato limpio.

---

## Características

- Monitorización de decenas de artistas de la escena urbana cubana
- Detección de lanzamientos nuevos (singles, EPs, álbumes)
- Publicación automática con portada + caption + preview de audio
- Sistema de estado persistente para evitar duplicados y permitir reanudar publicaciones interrumpidas
- Ejecución continua mediante GitHub Actions (ciclo de ~5 h 35 min que se auto-relanza)
- Soporte multi-fuente: YouTube Music + Deezer + Apple Music (previews)

---

## Estructura del proyecto

```
cubaton-music-bot/
├── bot.py                      # Orquestador principal
├── config.py                   # Configuración centralizada
├── artists.py                  # Lista de artistas monitorizados
├── logging_setup.py            # Logging estructurado (INFO/WARNING/ERROR)
├── apple_music_search.py       # Búsqueda de previews en Apple Music
├── youtube_music_search.py     # Búsqueda en YouTube Music
├── deezer_extractor.py         # Extracción de datos de Deezer
├── telegram_formatter.py       # Construcción de mensajes de Telegram
├── telegram_publisher.py       # Envío a Telegram + estado de publicación
├── publication_state.py        # Gestor de estado de publicaciones (portada/preview)
├── data/
│   └── publication_state.json  # Estado de mensajes enviados
├── state/
│   └── releases.json           # Canciones ya detectadas / publicadas
└── .github/workflows/          # Automatización con GitHub Actions
```

---

## Configuración

### Secrets necesarios (GitHub Actions)

| Secret                    | Descripción                                      |
|---------------------------|--------------------------------------------------|
| `TELEGRAM_BOT_TOKEN`      | Token del bot de Telegram                        |
| `TELEGRAM_CHAT_ID`        | (Opcional) Chat ID para alertas de errores       |

El canal de publicación está fijado en `config.py` como `@Cubaton_Music`.

### Variables importantes en `config.py`

| Variable                      | Descripción                                      | Valor por defecto |
|-------------------------------|--------------------------------------------------|-------------------|
| `MAX_ANTIGUEDAD_ANIOS`        | Solo publica canciones del año actual ± N        | `1`               |
| `PUBLICAR_SIN_PORTADA_SI_FALLA` | Publica aunque no se encuentre portada         | `True`            |
| `ENVIAR_PREVIEW_AUDIO`        | Envía adelanto de ~30 s                          | `True`            |
| `BOTON_EN_POST`               | Botón de YouTube Music en el post principal      | `False`           |
| `PAUSA_ENTRE_PUBLICACIONES`   | Segundos entre publicaciones                     | `2`               |
| `BUSCAR_COLABORACIONES`       | Buscar colaboraciones en otros canales           | `False`           |
| `BUSCAR_EN_DEEZER`            | Detectar también en Deezer                       | `False`           |

### Logging

Puedes controlar el nivel de log con la variable de entorno `LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Por defecto es `INFO`.

```python
from logging_setup import get_logger
log = get_logger(__name__)
log.info("Bot iniciado")
```

---

## Añadir un artista nuevo

Edita `artists.py` y añade un diccionario a la lista `ARTISTAS`:

```python
{
    "nombre": "Nombre del Artista",
    "deezer_id": "123456789",          # recomendado
    "channel_id": "UCxxxxxxxxxxxxxxxx", # canal de YouTube Music
},
```

También puedes usar `handle` (`@usuario`) y el bot resolverá el `channel_id` al arrancar.

Tras el primer ciclo, el bot registrará todo el catálogo histórico del artista **sin publicarlo** (línea base). A partir de ahí solo publicará lo nuevo.

---

## Ejecución local

```bash
git clone https://github.com/iLachy/cubaton-music-bot.git
cd cubaton-music-bot

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

export TELEGRAM_BOT_TOKEN="tu_token"
# opcional:
export TELEGRAM_CHAT_ID="tu_chat_id_de_alertas"
export LOG_LEVEL=INFO

python bot.py
```

> **Nota:** En local el bot hace una sola pasada. En producción el workflow de GitHub Actions lo ejecuta en bucle.

---

## GitHub Actions

El workflow principal (`.github/workflows/test.yml`) se ejecuta:

- Por cron cada hora (red de seguridad)
- Manualmente (`workflow_dispatch`)

Dentro del job corre un ciclo de ~5 h 35 min que lanza el bot cada 5 minutos y, al terminar, se auto-relanza. El estado (`state/releases.json`) se guarda en el propio repositorio tras cada ejecución.

---

## Scripts auxiliares

| Script                    | Uso                                              |
|---------------------------|--------------------------------------------------|
| `telegram_formatter.py`   | Genera los mensajes a partir de un JSON de datos |
| `telegram_publisher.py`   | Publica mensajes ya formateados (soporta reanudación) |
| `publication_state.py`    | Lógica de estado de portada/preview              |
| `logging_setup.py`        | Configuración de logging estructurado            |
| `deezer_debug.py`         | Utilidad de depuración de Deezer                 |

---

## Licencia

Uso personal / del canal @Cubaton_Music.
