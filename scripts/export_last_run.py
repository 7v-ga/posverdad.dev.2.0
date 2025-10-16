import os
import json
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

RUN_ID = os.getenv("LAST_RUN_ID")
if not RUN_ID:
    print("❌ LAST_RUN_ID no definido.")
    exit(1)

# === DB engine (SQLAlchemy) ===
db_url = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB')}"
)
engine = create_engine(db_url)

def get_articles():
    query = "SELECT * FROM articles WHERE run_id = :run_id ORDER BY publication_date DESC;"
    return pd.read_sql(text(query), engine, params={"run_id": RUN_ID})

def get_related_map(table, join_table, join_field):
    query = f"""
        SELECT a.article_id, b.{join_field}
        FROM articles_{table} AS a
        JOIN {table} AS b ON a.{table[:-1]}_id = b.id
        WHERE a.article_id IN (
            SELECT id FROM articles WHERE run_id = :run_id
        );
    """
    df = pd.read_sql(text(query), engine, params={"run_id": RUN_ID})
    mapping = df.groupby("article_id")[join_field].apply(list).to_dict()
    return mapping

def get_framing_map():
    query = """
        SELECT article_id, ideological_frame, actors, victims,
               antagonists, emotions, framing_summary
        FROM framing_analysis
        WHERE article_id IN (
            SELECT id FROM articles WHERE run_id = :run_id
        );
    """
    df = pd.read_sql(text(query), engine, params={"run_id": RUN_ID})
    return df.set_index("article_id").to_dict(orient="index")

def enrich_articles(articles):
    authors = get_related_map("authors", "name")
    keywords = get_related_map("keywords", "word")
    entities = get_related_map("entities", "name")
    framings = get_framing_map()

    enriched = []
    for _, row in articles.iterrows():
        article = row.to_dict()
        aid = article["id"]

        article["authors"] = authors.get(aid, [])
        article["keywords"] = keywords.get(aid, [])
        article["entities"] = entities.get(aid, [])
        article["framing"] = framings.get(aid, {})

        enriched.append(article)
    return enriched

def save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Exportado a {filename}")

if __name__ == "__main__":
    try:
        articles = get_articles()
        if articles.empty:
            print(f"⚠️ No hay artículos para run_id = {RUN_ID}")
            exit(0)

        enriched = enrich_articles(articles)
        fname = f"export_run_{RUN_ID}.json"
        save_json(enriched, fname)

    except Exception as e:
        print(f"❌ Error general: {e}")
