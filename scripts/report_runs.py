# scripts/report_runs.py

import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv

# === Configuración ===
load_dotenv()
db_url = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB')}"
)
engine = create_engine(db_url)

def parse_args():
    parser = argparse.ArgumentParser(description="📊 Reporte de ejecuciones NLP Posverdad")
    parser.add_argument("--desde", type=str, help="Fecha mínima (YYYY-MM-DD)")
    parser.add_argument("--hasta", type=str, help="Fecha máxima (YYYY-MM-DD)")
    parser.add_argument("--export", type=str, help="Ruta para exportar CSV")
    parser.add_argument("--detalles", action="store_true", help="Mostrar columnas adicionales")
    parser.add_argument("--nograph", action="store_true", help="No generar gráficos")
    parser.add_argument("--diagnostico", action="store_true", help="Analizar outliers y errores")
    parser.add_argument("--logfile", action="store_true", help="Usar logs/runs.log en vez de la base de datos")
    return parser.parse_args()

def cargar_runs(desde=None, hasta=None):
    filtros = []
    if desde:
        filtros.append(f"date >= '{desde}'")
    if hasta:
        filtros.append(f"date <= '{hasta}'")
    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    query = f"""
        SELECT run_id, date::timestamp(0), total_inserted, total_discarded,
               total_errors, duration_seconds
        FROM nlp_runs
        {where}
        ORDER BY date DESC
    """
    return pd.read_sql(query, engine)

def cargar_runs_desde_log():
    path = "logs/runs.log"
    if not os.path.exists(path):
        print("⚠️ No se encontró logs/runs.log")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["run_id"].str[:15], format="%Y%m%d-%H%M%S", errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values("date", ascending=False)
    return df

def mostrar_tabla(df, detalles=False):
    if df.empty:
        print("⚠️ No se encontraron ejecuciones.")
        return
    if not detalles:
        df = df[["run_id", "date", "insertados" if "insertados" in df.columns else "total_inserted",
                 "errores" if "errores" in df.columns else "total_errors",
                 "duracion_segundos" if "duracion_segundos" in df.columns else "duration_seconds"]]
    print(df.to_markdown(index=False))

def generar_graficos(df):
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["date"])
    df = df.sort_values("fecha")
    os.makedirs("graphs", exist_ok=True)

    y_insertados = df["insertados"] if "insertados" in df.columns else df["total_inserted"]
    y_duracion = df["duracion_segundos"] if "duracion_segundos" in df.columns else df["duration_seconds"]

    plt.figure(figsize=(10, 4))
    plt.plot(df["fecha"], y_insertados, marker='o')
    plt.title("📈 Artículos insertados por ejecución")
    plt.ylabel("Insertados")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("graphs/runs_articulos_por_dia.png")

    plt.figure(figsize=(10, 4))
    plt.bar(df["fecha"], y_duracion)
    plt.title("⏱ Duración de ejecución (segundos)")
    plt.ylabel("Duración")
    plt.xlabel("Fecha")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("graphs/runs_duracion_por_dia.png")

def diagnostico(df):
    print("\n🔎 Diagnóstico automático de runs\n")
    col_ins = "insertados" if "insertados" in df.columns else "total_inserted"
    col_err = "errores" if "errores" in df.columns else "total_errors"
    col_dur = "duracion_segundos" if "duracion_segundos" in df.columns else "duration_seconds"

    vacíos = df[df[col_ins] == 0]
    if not vacíos.empty:
        print("❗ Runs sin artículos insertados:")
        print(vacíos[["run_id", "date", col_err, col_dur]].to_markdown(index=False))
    else:
        print("✅ No hay runs con 0 artículos insertados.")

    errores_muchos = df[df[col_err] > 50]
    if not errores_muchos.empty:
        print("\n⚠️ Runs con errores altos (> 50):")
        print(errores_muchos[["run_id", "date", col_err, col_ins]].to_markdown(index=False))

    dur_media = df[col_dur].mean()
    dur_std = df[col_dur].std()
    umbral = dur_media + 2 * dur_std
    outliers = df[df[col_dur] > umbral]
    if not outliers.empty:
        print(f"\n🐢 Runs con duración inusualmente alta (> {int(umbral)}s):")
        print(outliers[["run_id", "date", col_dur]].to_markdown(index=False))

def main():
    args = parse_args()
    try:
        if args.logfile:
            df = cargar_runs_desde_log()
        else:
            df = cargar_runs(desde=args.desde, hasta=args.hasta)

        mostrar_tabla(df, detalles=args.detalles)

        if args.export:
            df.to_csv(args.export, index=False)
            print(f"\n📤 Exportado a: {args.export}")

        if args.diagnostico:
            diagnostico(df)

        if not args.nograph and not df.empty:
            generar_graficos(df)
            print("📈 Gráficos generados en carpeta 'graphs/'")

    except Exception as e:
        print(f"❌ Error en reporte: {e}")

if __name__ == "__main__":
    main()
