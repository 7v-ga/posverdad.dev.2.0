# scripts/check_vacios.py

import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from dotenv import load_dotenv

# === Configuración ===
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

DB_URL = (
    f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB')}"
)
engine = create_engine(DB_URL)

# === Función para alerta Slack ===
def slack_alert(text, title="🚨 Run vacío detectado"):
    if not SLACK_WEBHOOK_URL:
        return
    payload = {"text": f"*{title}*\n{text}"}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f"⚠️ Error al enviar a Slack: {response.text}")
    except Exception as e:
        print(f"❌ Excepción enviando alerta Slack: {e}")

# === Cargar y filtrar ===
def cargar_runs():
    query = """
        SELECT run_id, date::timestamp(0), total_inserted
        FROM nlp_runs
        ORDER BY date DESC
    """
    return pd.read_sql(query, engine)

def check_vacios(dias=3):
    try:
        df = cargar_runs()
        if df.empty:
            print("⚠️ No hay datos en nlp_runs.")
            return

        recientes = df[df["date"] >= datetime.now() - timedelta(days=dias)]
        vacios = recientes[recientes["total_inserted"] == 0]

        if vacios.empty:
            print(f"🟢 Sin runs vacíos en los últimos {dias} días.")
        else:
            print(f"\n🚨 Se encontraron {len(vacios)} run(s) vacíos en los últimos {dias} días:")
            print(vacios[["run_id", "date"]].to_markdown(index=False))

            resumen = "\n".join(f"- {row['run_id']} ({row['date']})" for _, row in vacios.iterrows())
            slack_alert(resumen, title=f"🚨 {len(vacios)} run(s) vacíos en los últimos {dias} días")

    except Exception as e:
        print(f"❌ Error al verificar runs vacíos: {e}")

# === Punto de entrada ===
if __name__ == "__main__":
    check_vacios(dias=3)
