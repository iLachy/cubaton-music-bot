import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL = "@Cubaton_Music"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {
    "chat_id": CHANNEL,
    "text": "🤖 Prueba automática\n\nCubaton Music está funcionando correctamente. 🇨🇺🎵"
}

response = requests.post(url, data=data)

if response.ok:
    print("✅ Mensaje enviado correctamente.")
else:
    print("❌ Error:", response.text)
    raise SystemExit(1)
