# scripts/nlp_warmup.py

"""
Descarga y verifica recursos NLP esenciales antes de correr el pipeline.
"""

def check_and_warmup_nlp(log=True):
    import importlib

    # --- spaCy ---
    try:
        import spacy
        spacy.load("es_core_news_md")
        if log:
            print("✅ spaCy: es_core_news_md disponible.")
    except Exception:
        import subprocess
        print("⬇️ Descargando spaCy es_core_news_md...")
        subprocess.run(["python", "-m", "spacy", "download", "es_core_news_md"], check=True)
        import spacy
        spacy.load("es_core_news_md")
        print("✅ spaCy es_core_news_md descargado y cacheado.")

    # --- pysentimiento SOLO sentiment para español ---
    try:
        from pysentimiento import create_analyzer
        print("Intentando descargar modelo sentiment (pysentimiento)...")
        create_analyzer(task="sentiment", lang="es")
        print("Sentiment descargado OK")
        if log:
            print("✅ pysentimiento: modelo español (sentiment) listo.")
    except Exception as e:
        print("❌ Error descargando modelos pysentimiento:")
        print(repr(e))
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    check_and_warmup_nlp()
