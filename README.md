# Cubaton Music Bot

Bot de Telegram que monitoriza lanzamientos de música urbana cubana y los publica automáticamente en [@Cubaton_Music](https://t.me/Cubaton_Music).

La fuente principal de detección es YouTube Music. Los previews se buscan primero en Apple Music y, si no están disponibles, en Deezer.

## Funcionamiento

1. GitHub Actions inicia el bot por programación horaria o manualmente.
2. El bot consulta los artistas configurados y detecta canciones nuevas.
3. Obtiene los metadatos y prepara la portada y, cuando existe, un preview de audio.
4. Publica cada canción de forma secuencial:
   - Mensaje principal con portada y caption.
   - Mensaje independiente con el preview y el botón de escucha, cuando hay preview.
5. Guarda el estado de cada mensaje y sincroniza los archivos de estado con GitHub.

El workflow de producción es `.github/workflows/run-bot.yml`. Ejecuta ciclos de aproximadamente 5 horas y 35 minutos, consulta el catálogo cada 5 minutos y se relanza al terminar. También tiene una ejecución horaria de seguridad. La concurrencia está limitada para evitar dos ciclos simultáneos.

## Recuperación y prevención de duplicados

El estado de detección y el estado de publicación se guardan por separado:

| Archivo | Contenido |
|---|---|
| `state/releases.json` | Claves de canciones ya completadas o registradas como históricas. |
| `state/telegram_messages.json` | Estado individual de portada y preview, con sus respectivos `message_id`. |

Cada canción conserva dos pasos independientes:

- `cover`: portada/caption o mensaje de texto alternativo.
- `preview`: audio preview o estado terminal `not_available` cuando no existe un preview utilizable.

Los estados de cada paso son `pending`, `sending`, `sent`, `failed`, `unknown` o, para el preview, `not_available`.

**Reanudación normal:** si la portada ya se publicó y el preview falló, el siguiente ciclo conserva el `message_id` de la portada y vuelve a intentar únicamente el preview. La canción no se incorpora al registro de canciones completadas hasta que ambos pasos estén resueltos.

**Envío ambiguo:** si el proceso se interrumpe durante una petición o se pierde la respuesta de Telegram, el paso pasa a `unknown`. No se reenvía automáticamente, porque Telegram podría haber recibido el mensaje. Antes de reintentar, hay que comprobar el canal y resolver manualmente ese registro.

Ambos archivos se escriben mediante reemplazo atómico. Si un archivo de estado existente está corrupto o tiene una versión incompatible, el bot se detiene: no crea una línea base nueva ni sobrescribe el estado dudoso.

## Configuración

### Secrets de GitHub Actions

| Secret | Obligatorio | Descripción |
|---|---:|---|
| `TELEGRAM_BOT_TOKEN` | Sí | Token del bot de Telegram. |
| `TELEGRAM_ALERT_CHAT_ID` | No | Chat privado que recibe alertas de errores. |

Por compatibilidad, `config.py` también acepta `TELEGRAM_CHAT_ID` como nombre alternativo antiguo para el chat de alertas. El canal de publicación está fijado en `config.py` como `@Cubaton_Music`.

### Variables de configuración

| Variable | Descripción | Valor actual |
|---|---|---|
| `MAX_ANTIGUEDAD_ANIOS` | Antigüedad máxima de las canciones publicables. | `1` |
| `PUBLICAR_SIN_PORTADA_SI_FALLA` | Permite publicar el mensaje de texto si no se consigue una portada. | `True` |
| `ENVIAR_PREVIEW_AUDIO` | Habilita la búsqueda y publicación de previews. | `True` |
| `BOTON_EN_POST` | Añade también el botón de escucha al mensaje principal. | `False` |
| `PAUSA_ENTRE_PUBLICACIONES` | Pausa entre canciones. | `2` segundos |
| `BUSCAR_COLABORACIONES` | Busca colaboraciones en canales de otros artistas. | `False` |
| `BUSCAR_EN_DEEZER` | Habilita Deezer como fuente adicional de detección. | `False` |

## Estructura relevante

```
cubaton-music-bot/
├── bot.py
├── config.py
├── artists.py
├── logging_setup.py
├── telegram_message_state.py
├── state/
│   ├── releases.json
│   └── telegram_messages.json
├── tests/
│   ├── test_release_state.py
│   ├── test_telegram_message_state.py
│   └── test_telegram_send_tracking.py
└── .github/
    └── workflows/
        ├── run-bot.yml
        └── test-publication-state.yml
```

Los módulos `telegram_publisher.py`, `telegram_formatter.py` y `publication_state.py` pertenecen a una implementación anterior. El flujo de producción actual está orquestado directamente por `bot.py` y utiliza `telegram_message_state.py` para el estado granular.

## Pruebas

Las pruebas automatizadas no envían mensajes a Telegram. Utilizan archivos temporales y respuestas simuladas.

Para ejecutarlas localmente:

```bash
pip install -r requirements.txt
python -m py_compile bot.py telegram_message_state.py
python -m unittest discover -s tests -v
```

El workflow `.github/workflows/test-publication-state.yml` ejecuta estas validaciones al actualizar ramas `fix/**`, al abrir o actualizar un pull request hacia `main`, o manualmente.

## Añadir un artista

Edita `artists.py` y añade un diccionario a `ARTISTAS`:

```python
{
    "nombre": "Nombre del Artista",
    "deezer_id": "123456789",
    "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
}
```

También se puede configurar un `handle` (`@usuario`) para que el bot intente resolver el `channel_id` al iniciar.

En la primera ejecución de un artista nuevo, el bot registra su catálogo existente como línea base y no lo publica. A partir de entonces, procesa los lanzamientos nuevos.

## Logging y alertas

El nivel de logging se puede controlar mediante `LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING` o `ERROR`). El valor predeterminado es `INFO`.

Las alertas privadas son opcionales. Si no se configura un chat de alertas, los errores siguen apareciendo en los logs de GitHub Actions.

## Licencia

Uso personal para el canal [@Cubaton_Music](https://t.me/Cubaton_Music).
