# preprocessor.py — Utilidades de preprocesamiento textual con spaCy o Stanza
# =============================================================================

import spacy

try:
    import stanza
    stanza_available = True
except ImportError:
    stanza_available = False


class Preprocessor:
    """
    Clase encargada de realizar preprocesamiento lingüístico básico sobre texto,
    utilizando spaCy o Stanza como backend NLP.
    """

    def __init__(self, engine="spacy"):
        self.engine = engine.lower()
        if self.engine == "spacy":
            self.nlp = spacy.load("es_core_news_md")
        elif self.engine == "stanza":
            if not stanza_available:
                raise ImportError("Stanza no está instalado. Usa: pip install stanza")
            stanza.download("es", verbose=False)
            self.nlp = stanza.Pipeline("es", processors="tokenize,pos,lemma", verbose=False)
        else:
            raise ValueError("Engine debe ser 'spacy' o 'stanza'.")

    def preprocess(self, text):
        """
        Aplica preprocesamiento NLP al texto:
        - Tokenización
        - Lematización
        - Etiquetado gramatical (POS)
        """
        if text is None:
            raise TypeError("El texto de entrada no puede ser None.")
        if not text.strip():
            return {
                "engine": self.engine,
                "tokens": [],
                "lemmas": [],
                "pos": [],
            }

        if self.engine == "spacy":
            return self._preprocess_spacy(text)
        elif self.engine == "stanza":
            return self._preprocess_stanza(text)

    def _preprocess_spacy(self, text):
        """
        Preprocesamiento con spaCy.
        Filtra signos de puntuación y stopwords.
        """
        doc = self.nlp(text)
        tokens = []
        lemmas = []
        pos_tags = []

        for token in doc:
            if not token.is_stop and not token.is_punct:
                tokens.append(token.text)
                lemmas.append(token.lemma_)
                pos_tags.append(token.pos_)

        return {
            "engine": "spacy",
            "tokens": tokens,
            "lemmas": lemmas,
            "pos": pos_tags,
        }

    def _preprocess_stanza(self, text):
        """
        Preprocesamiento con Stanza.
        Filtra algunos signos de puntuación básicos.
        """
        doc = self.nlp(text)
        tokens = []
        lemmas = []
        pos_tags = []

        for sentence in doc.sentences:
            for word in sentence.words:
                if word.text not in {".", ",", ";", ":", "¿", "?", "¡", "!"}:
                    tokens.append(word.text)
                    lemmas.append(word.lemma)
                    pos_tags.append(word.upos)

        return {
            "engine": "stanza",
            "tokens": tokens,
            "lemmas": lemmas,
            "pos": pos_tags,
        }
