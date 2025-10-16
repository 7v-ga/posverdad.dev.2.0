# scripts/report_summary.py

import os
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sqlalchemy import create_engine

# === Configuración ===
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"
plt.rcParams["font.size"] = 9

N = int(os.getenv("SUMMARY_RUNS_LIMIT", "30"))
EXPORT_HTML = True

db_url = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB')}"
)

engine = create_engine(db_url)

def generar_graficos(df):
    os.makedirs("graphs", exist_ok=True)

    # Artículos por día
    plt.figure(figsize=(8, 4))
    plt.plot(df['fecha'], df['total_inserted'], marker='o')
    plt.title("📈 Artículos por día")
    plt.xlabel("Fecha")
    plt.ylabel("Insertados")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("graphs/summary_articulos_por_dia.png")
    print("✅ Gráfico de artículos generado.")

    # Duración por día
    plt.figure(figsize=(8, 4))
    plt.bar(df['fecha'], df['duration_seconds'])
    plt.title("⏱ Duración por día")
    plt.xlabel("Fecha")
    plt.ylabel("Segundos")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("graphs/summary_duracion_por_dia.png")
    print("✅ Gráfico de duración generado.")

def top_errores(df):
    print("\n❗ Top 5 runs con más errores:")
    top = df.sort_values(by="total_errors", ascending=False).head(5)
    print(top[['run_id', 'fecha', 'total_inserted', 'total_errors', 'duration_seconds']])
    return top

def resumen_tabular(df):
    resumen = df.describe(include='all').transpose()
    print("\n📊 Resumen estadístico:")
    print(resumen[['count', 'mean', 'min', 'max']])

def resumen_por_categoria():
    try:
        df_cat = pd.read_sql("""
            SELECT category, COUNT(*) as total
            FROM articles
            WHERE run_id IS NOT NULL
            GROUP BY category
            ORDER BY total DESC
            LIMIT 10;
        """, engine)
        print("\n📚 Artículos por categoría:")
        print(df_cat)
        df_cat.to_csv("graphs/summary_por_categoria.csv", index=False)

        plt.figure(figsize=(8, 4))
        plt.barh(df_cat['category'], df_cat['total'])
        plt.title("📚 Top categorías (últimos artículos)")
        plt.tight_layout()
        plt.savefig("graphs/summary_categorias.png")
        print("✅ Gráfico de categorías generado.")

        return df_cat

    except Exception as e:
        print(f"⚠️ No se pudo generar resumen por categoría: {e}")
        return None

def exportar_html(df, top_errores_df, categorias_df=None):
    try:
        html = "<h1>Resumen Postverdad</h1>\n"

        html += "<h2>Últimos runs</h2>\n"
        html += df.to_html(index=False)

        html += "<h2>Top 5 errores</h2>\n"
        html += top_errores_df.to_html(index=False)

        if categorias_df is not None:
            html += "<h2>Artículos por categoría</h2>\n"
            html += categorias_df.to_html(index=False)

        output_path = "graphs/summary_report.html"
        with open(output_path, "w") as f:
            f.write(html)
        print(f"🌐 HTML generado en {output_path}")

    except Exception as e:
        print(f"❌ Error generando HTML: {e}")

def main():
    try:
        df = pd.read_sql(f"""
            SELECT run_id, date::date AS fecha, total_inserted,
                   total_discarded, total_errors, duration_seconds
            FROM nlp_runs
            WHERE total_inserted IS NOT NULL
            ORDER BY date DESC
            LIMIT {N}
        """, engine)

        if df.empty:
            print("⚠️ No hay runs disponibles.")
            return

        df['fecha'] = pd.to_datetime(df['fecha'])

        resumen_tabular(df)
        generar_graficos(df)
        top_df = top_errores(df)
        cat_df = resumen_por_categoria()

        df.to_csv("graphs/summary_last_runs.csv", index=False)

        if EXPORT_HTML:
            exportar_html(df, top_df, cat_df)

    except Exception as e:
        print(f"❌ Error generando resumen: {e}")

if __name__ == "__main__":
    main()
