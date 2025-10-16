# test_nlp_orchestrator.py — Pruebas unitarias básicas para NLPOrchestrator
# =================================================================

import unittest
from unittest.mock import MagicMock
from scrapy_project.nlp_orchestrator import NLPOrchestrator

class TestNLPOrchestrator(unittest.TestCase):

    def setUp(self):
        # Mocks de los componentes internos
        self.mock_spacy = MagicMock()
        self.mock_spacy.return_value.ents = []

        self.mock_postverdad_nlp = MagicMock()
        self.mock_postverdad_nlp.analyze_sentiment.return_value = (0.5, "NEUTRAL")
        self.mock_postverdad_nlp.subjectivity_proxy.return_value = 0.6

        self.mock_framing = MagicMock()
        self.mock_framing.analyze_framing.return_value = {"ideological_frame": "neutral"}

        self.mock_preprocessor = MagicMock()
        self.mock_preprocessor.preprocess.return_value = {"tokens": ["hola", "mundo"]}

        self.orchestrator = NLPOrchestrator(
            spacy_model=self.mock_spacy,
            postverdad_nlp=self.mock_postverdad_nlp,
            framing_analyzer=self.mock_framing,
            preprocessor=self.mock_preprocessor
        )

    def test_analyze_text(self):
        texto = "Gabriel Boric es presidente de Chile."
        result = self.orchestrator.analyze(texto)

        self.assertIn("polarity", result)
        self.assertIn("subjectivity", result)
        self.assertIn("entities", result)
        self.assertIn("framing", result)
        self.assertIn("preprocessed", result)

        self.assertEqual(result["polarity"], 0.5)
        self.assertEqual(result["subjectivity"], 0.6)
        self.assertEqual(result["framing"], {"ideological_frame": "neutral"})
        self.assertEqual(result["preprocessed"], {"tokens": ["hola", "mundo"]})

    def test_empty_text(self):
        result = self.orchestrator.analyze("")
        self.assertEqual(result["entities"], [])
        self.assertEqual(result["preprocessed"], {})

if __name__ == '__main__':
    unittest.main()
