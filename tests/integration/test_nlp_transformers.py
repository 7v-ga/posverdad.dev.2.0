# test_nlp_transformers.py — Pruebas unitarias para PostverdadNLP
# ===============================================================

import unittest
from unittest.mock import MagicMock
from scrapy_project.nlp_transformers import PostverdadNLP

class TestPostverdadNLP(unittest.TestCase):

    def setUp(self):
        # Crea una instancia sin spaCy para pruebas individuales
        self.nlp = PostverdadNLP(nlp_model=None)
        self.nlp.sa = MagicMock()

    def test_analyze_sentiment_positive(self):
        self.nlp.sa.predict.return_value.output = "POS"
        self.nlp.sa.predict.return_value.probas = {"POS": 0.88}
        polarity, score = self.nlp.analyze_sentiment("Me encanta este proyecto")
        self.assertEqual(polarity, 1.0)
        self.assertAlmostEqual(score, 0.88)

    def test_analyze_sentiment_negative(self):
        self.nlp.sa.predict.return_value.output = "NEG"
        self.nlp.sa.predict.return_value.probas = {"NEG": 0.77}
        polarity, score = self.nlp.analyze_sentiment("Esto es un desastre")
        self.assertEqual(polarity, -1.0)
        self.assertAlmostEqual(score, 0.77)

    def test_analyze_sentiment_empty_text(self):
        polarity, score = self.nlp.analyze_sentiment("   ")
        self.assertIsNone(polarity)
        self.assertIsNone(score)

    def test_subjectivity_proxy_with_spacy(self):
        # Mock de spaCy para evitar dependencia real
        mock_doc = [MagicMock(pos_="ADJ", dep_="amod")] * 5 + [MagicMock(pos_="NOUN", dep_="nsubj")] * 5
        self.nlp.spacy = MagicMock(return_value=mock_doc)
        subjectivity = self.nlp.subjectivity_proxy("Texto de prueba")
        self.assertEqual(subjectivity, 0.5)

    def test_subjectivity_proxy_no_model(self):
        self.nlp.spacy = None
        result = self.nlp.subjectivity_proxy("texto")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
