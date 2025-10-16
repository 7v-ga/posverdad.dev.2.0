import os
import json
import requests
import argparse
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_slack_alert(message, title="🚨 Test Notificación", debug=False):
    if not SLACK_WEBHOOK_URL or not SLACK_WEBHOOK_URL.startswith("https://hooks.slack.com/"):
        print("❌ SLACK_WEBHOOK_URL no está definido correctamente en .env")
        return

    payload = {
        "text": f"*{title}*\n{message}"
    }

    if debug:
        print("🔧 Debug:")
        print(f"➡️ Webhook URL: {SLACK_WEBHOOK_URL}")
        print(f"➡️ Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if debug:
            os.makedirs("logs", exist_ok=True)
            debug_path = "logs/slack_debug.json"
            with open(debug_path, "w") as f:
                json.dump({
                    "status_code": response.status_code,
                    "response_text": response.text
                }, f, indent=2)
            print(f"📝 Respuesta de Slack guardada en {debug_path}")

        if response.status_code == 200 and response.text.strip() == "ok":
            print("✅ Notificación enviada a Slack.")
        else:
            print(f"❌ Error al enviar notificación: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción al enviar notificación: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Activa salida en modo debug")
    args = parser.parse_args()

    send_slack_alert("Este es un test de notificación crítica desde Makefile.", debug=args.debug)
