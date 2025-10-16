# nlp_transformers.py — Módulo de análisis NLP básico basado en pysentimiento y spaCy
# ====================================================================================

from pysentimiento import create_analyzer


class PostverdadNLP:
    """
    Clase que encapsula análisis de sentimiento y una estimación heurística de subjetividad
    usando modelos entrenados para español. Se apoya en pysentimiento para sentimiento
    y en spaCy para análisis morfosintáctico.
    """
    def __init__(self, nlp_model=None):
        self.spacy = nlp_model  # Debe pasarse una instancia spaCy ya cargada

        try:
            self.sa = create_analyzer(task="sentiment", lang="es")
        except Exception as e:
            print(f"[ERROR] No se pudo cargar el analizador de sentimiento: {e}")
            self.sa = None

        # Eliminado: subjectivity como tarea no está soportada por pysentimiento en español
        self.subj = None

    def analyze_sentiment(self, text):
        """
        Ejecuta análisis de sentimiento y retorna una tupla (polaridad, score).
        
        - `polarity`: 1.0 (positivo), 0.0 (neutral), -1.0 (negativo)
        - `score`: confianza/probabilidad de la clase asignada (float entre 0 y 1)

        Retorna (None, None) si falla.
        """
        if not self.sa or not text or not text.strip():
            return None, None

        try:
            result = self.sa.predict(text)
            polarity_map = {"POS": 1.0, "NEU": 0.0, "NEG": -1.0}
            polarity = polarity_map.get(result.output, 0.0)
            score = float(result.probas.get(result.output, 0.0))
            return polarity, score
        except Exception as e:
            print(f"[ERROR] Fallo en análisis de sentimiento: {e}")
            return None, None

    def subjectivity_proxy(self, text):
        """
        Calcula una estimación simple de subjetividad basada en la proporción de
        adjetivos y verbos subordinados (como modales o relativos).

        Requiere un modelo spaCy cargado. Retorna float entre 0 y 1.
        """
        if not self.spacy or not text.strip():
            return None

        try:
            doc = self.spacy(text)
            subj_words = [
                token for token in doc
                if token.pos_ in {"ADJ", "VERB"} and token.dep_ in {"amod", "acomp", "advcl", "relcl"}
            ]
            return round(len(subj_words) / len(doc), 4) if len(doc) > 0 else 0
        except Exception as e:
            print(f"[ERROR] Fallo en cálculo de subjetividad: {e}")
            return None
