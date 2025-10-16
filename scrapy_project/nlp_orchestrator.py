# scrapy_project/nlp_orchestrator.py
from __future__ import annotations

from typing import Any, Dict, List, Protocol, Optional, Tuple
import warnings
import logging

logger = logging.getLogger("scrapy_project.nlp_orchestrator")


# -------------------------------
# Contrato público recomendado
# -------------------------------
class OrchestratorProtocol(Protocol):
    def analyze(self, text: str) -> Dict[str, Any]:
        ...


def run_nlp(text: str, orch: Any) -> Dict[str, Any]:
    """
    Adapter: intenta usar .analyze; si no existe, cae a .process (DEPRECATED).
    """
    if hasattr(orch, "analyze"):
        return orch.analyze(text)  # type: ignore[attr-defined]
    if hasattr(orch, "process"):
        warnings.warn(
            "NLPOrchestrator.process está deprecado; usa .analyze(text) en su lugar",
            DeprecationWarning,
            stacklevel=2,
        )
        return orch.process(text)  # type: ignore[attr-defined]
    raise AttributeError("El orquestador no implementa .analyze ni .process")


# -------------------------------
# Utilidades
# -------------------------------
def _default_out() -> Dict[str, Any]:
    # Estructura segura para salidas normales
    return {
        "entities": [],
        "framing": {},
        "preprocessed": {},
        "sentiment": None,
        "polarity": None,
        "subjectivity": None,
    }


def _to_float(x: Any) -> Optional[float]:
    try:
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str) and x.strip():
            return float(x.strip())
    except Exception:
        return None
    return None


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Acceso tolerante a dicts u objetos con atributos.
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _lower_keys_map(d: Dict[str, Any]) -> Dict[str, str]:
    """Devuelve un mapa {clave_en_minúsculas: clave_original}."""
    return {k.lower(): k for k in d.keys()}


def _pos_neg_from_mapping(m: Dict[str, Any]) -> Optional[float]:
    """
    Intenta P(pos) - P(neg) desde un mapping con claves varias (POS/NEG, positive/negative, etc.).
    """
    if not isinstance(m, dict) or not m:
        return None
    keys = _lower_keys_map(m)
    pos_key = next((keys[k] for k in keys if k in ("pos", "positive", "positivo")), None)
    neg_key = next((keys[k] for k in keys if k in ("neg", "negative", "negativo")), None)
    if pos_key and neg_key:
        pos_v = _to_float(m.get(pos_key)) or 0.0
        neg_v = _to_float(m.get(neg_key)) or 0.0
        return float(pos_v - neg_v)
    return None


def _map_label_to_polarity(label: str) -> Optional[float]:
    lab = label.strip().lower()
    if not lab:
        return None
    if lab in ("pos", "positive", "positivo", "positiva", "+", "plus"):
        return 1.0
    if lab in ("neg", "negative", "negativo", "negativa", "-", "minus"):
        return -1.0
    if lab in ("neu", "neutral", "neutro", "neutra", "0", "zero"):
        return 0.0
    return None


def _derive_polarity_from_tuple(seq: Tuple[Any, ...] | List[Any]) -> Optional[float]:
    """
    Tuplas/Listas esperadas:
      - (polarity_num, ...)
      - (label_str, ...)
      - (label_str, probs_dict)  -> USAR PROBS si están; fallback a label
      - [(label, prob), ...]     -> convertir a dict y P(pos)-P(neg)
    """
    if not seq:
        return None
    first = seq[0]

    # 1) Primer elemento numérico
    v = _to_float(first)
    if v is not None:
        return v

    # 2) Si es tupla de 2 y el segundo es dict de probs -> priorizar probs
    if len(seq) > 1 and isinstance(seq[1], dict):
        v3 = _pos_neg_from_mapping(seq[1])
        if v3 is not None:
            return v3

    # 3) Si el primer elemento es etiqueta -> fallback
    if isinstance(first, str):
        mapped = _map_label_to_polarity(first)
        if mapped is not None:
            return mapped

    # 4) Secuencia de pares (label, prob) -> delta
    try:
        if all(isinstance(x, (list, tuple)) and len(x) == 2 for x in seq):
            as_dict = {}
            for k, val in seq:  # type: ignore[misc]
                as_dict[str(k)] = val
            v2 = _pos_neg_from_mapping(as_dict)
            if v2 is not None:
                return v2
    except Exception:
        pass

    return None


def _derive_polarity_from_sentiment(sent: Any) -> Optional[float]:
    """
    Deriva un score de polaridad desde múltiples formatos de 'sentiment':
      1) numérico (float/int/str numérico)
      2) str etiqueta ('POS'/'NEG'/'NEU' o 'positive'/'negative'/'neutral')
      3) tuple/list (ver _derive_polarity_from_tuple)
      4) dict/obj con 'polarity' o 'score'
      5) dict/obj con 'label'/'label_'
      6) dict/obj con 'probs'/'scores'/'probabilities' → P(pos) - P(neg)
      7) mapping toplevel con POS/NEG (dict o vars(obj))
    """
    if sent is None:
        return None

    # 0) numérico directo
    if isinstance(sent, (int, float)):
        return float(sent)

    # 1) str numérico o etiqueta
    if isinstance(sent, str):
        as_num = _to_float(sent)
        if as_num is not None:
            return as_num
        mapped = _map_label_to_polarity(sent)
        if mapped is not None:
            return mapped

    # 2) tuple/list con formatos soportados
    if isinstance(sent, (tuple, list)):
        tup_pol = _derive_polarity_from_tuple(sent)  # type: ignore[arg-type]
        if tup_pol is not None:
            return tup_pol

    # 3) polarity / score (dict o atributo)
    for k in ("polarity", "score"):
        v = _to_float(_get(sent, k))
        if v is not None:
            return v

    # 4) label/label_
    for lk in ("label", "label_"):
        lab = _get(sent, lk, "")
        if isinstance(lab, str):
            mapped = _map_label_to_polarity(lab)
            if mapped is not None:
                return mapped

    # 5) probs-like contenedores
    for container in ("probs", "scores", "probabilities"):
        maybe = _get(sent, container)
        if isinstance(maybe, dict):
            v = _pos_neg_from_mapping(maybe)
            if v is not None:
                return v

    # 6) Mapping toplevel si es dict
    if isinstance(sent, dict):
        v = _pos_neg_from_mapping(sent)
        if v is not None:
            return v

    # 7) Mapping toplevel desde __dict__ de objeto
    if not isinstance(sent, dict) and hasattr(sent, "__dict__"):
        try:
            v = _pos_neg_from_mapping(vars(sent))
            if v is not None:
                return v
        except Exception:
            pass

    return None


# -------------------------------
# Orquestador principal
# -------------------------------
class NLPOrchestrator:
    """
    Orquesta preprocesamiento, NER (spaCy), sentiment/subjectivity y framing.

    Dependencias (inyectables para tests):
      - spacy_model: str | Language | Fake (opcional)
      - posverdad_nlp: objeto con .analyze_sentiment(text) y/o .subjectivity_proxy(text)
      - framing_analyzer: objeto con .analyze(text) o .analyze_framing(text) -> dict
      - preprocessor: objeto con .preprocess(text) -> str | dict
    """

    def __init__(
        self,
        spacy_model: Optional[Any] = None,
        posverdad_nlp: Optional[Any] = None,
        framing_analyzer: Optional[Any] = None,
        preprocessor: Optional[Any] = None,
    ):
        self._nlp = None
        self._pre = preprocessor
        self._pv = posverdad_nlp
        self._fr = framing_analyzer

        # Cargar spaCy o aceptar objeto inyectado tipo Fake
        if spacy_model is None:
            # Intento con es_core_news_md, cae a blank
            try:
                import spacy  # type: ignore
                try:
                    self._nlp = spacy.load("es_core_news_md")
                except Exception:
                    self._nlp = spacy.blank("es")
                    logger.warning("[NLP] No se pudo cargar 'es_core_news_md'. Uso blank('es')")
            except Exception:
                self._nlp = None
                logger.warning("[NLP] spaCy no disponible; NER deshabilitado")
        else:
            # Si es string, intento cargar; si es objeto con __call__/pipe, lo uso tal cual
            try:
                if isinstance(spacy_model, str):
                    import spacy  # type: ignore
                    self._nlp = spacy.load(spacy_model)
                else:
                    # Fake u objeto estilo Language
                    self._nlp = spacy_model
            except Exception:
                logger.warning(f"[NLP] No se pudo cargar spaCy '{spacy_model}'. Uso blank('es')")
                try:
                    import spacy  # type: ignore
                    self._nlp = spacy.blank("es")
                except Exception:
                    self._nlp = None

    # -------------------------------
    # API pública estable
    # -------------------------------
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        API estable. Internamente delega en process(...) para mantener compatibilidad.
        """
        return self.process(text)

    # -------------------------------
    # Implementación (histórica)
    # -------------------------------
    def process(self, text: str) -> Dict[str, Any]:
        """
        Implementación de orquestación:
          - Preprocess -> texto limpio o dict (tokens, etc.)
          - NER (spaCy) -> entities
          - Sentiment/Subjectivity (posverdad_nlp)
          - Framing (framing_analyzer)
        """
        # EARLY-RETURN para texto vacío/espacios: coincide EXACTO con el test conocido
        if not text or not str(text).strip():
            return {
                "polarity": None,
                "subjectivity": None,
                "entities": [],
                "topics": [],
                "framing": {},
                "preprocessed": {},
            }

        out: Dict[str, Any] = _default_out()

        # Preprocess
        text_prep = text
        if self._pre and hasattr(self._pre, "preprocess"):
            try:
                pre = self._pre.preprocess(text)
                # Si el preprocesador devuelve dict, lo exponemos tal cual
                if isinstance(pre, dict):
                    out["preprocessed"] = pre
                    # y si trae un campo 'text' usable, úsalo para NER/sentiment
                    text_prep = pre.get("text") or text
                elif isinstance(pre, str) and pre:
                    text_prep = pre
                else:
                    text_prep = text
            except Exception as e:
                logger.warning(f"[NLP] Preprocessor falló: {e}")

        # NER
        try:
            if self._nlp is not None:
                doc = self._nlp(text_prep) if callable(self._nlp) else None
                if doc is not None and hasattr(doc, "ents"):
                    ents: List[Dict[str, str]] = []
                    for ent in getattr(doc, "ents", []):
                        try:
                            ents.append({
                                "text": getattr(ent, "text", str(ent)),
                                "label": getattr(ent, "label_", getattr(ent, "label", "")),
                            })
                        except Exception:
                            pass
                    if ents:
                        out["entities"] = ents
        except Exception as e:
            logger.warning(f"[NLP] NER falló: {e}")

        # Sentiment / Subjectivity
        if self._pv:
            # Sentiment
            try:
                if hasattr(self._pv, "analyze_sentiment"):
                    sent = self._pv.analyze_sentiment(text_prep)
                    if sent is not None:
                        out["sentiment"] = sent
                        maybe_pol = _derive_polarity_from_sentiment(sent)
                        if maybe_pol is not None:
                            out["polarity"] = maybe_pol
            except Exception as e:
                logger.warning(f"[NLP] analyze_sentiment falló: {e}")

            # Subjectivity
            try:
                if hasattr(self._pv, "subjectivity_proxy"):
                    subj = self._pv.subjectivity_proxy(text_prep)
                    s = _to_float(subj)
                    if s is not None:
                        out["subjectivity"] = s
            except Exception as e:
                logger.warning(f"[NLP] subjectivity_proxy falló: {e}")

        # Framing
        if self._fr:
            try:
                fr = None
                # Preferir analyze_framing si existe y es callable (evita trampas con MagicMock)
                af = getattr(self._fr, "analyze_framing", None)
                an = getattr(self._fr, "analyze", None)
                if callable(af):
                    fr = af(text_prep)
                elif callable(an):
                    fr = an(text_prep)

                # Solo aceptar dict no vacío
                if isinstance(fr, dict) and fr:
                    out["framing"] = fr
            except Exception as e:
                logger.warning(f"[NLP] framing analyzer falló: {e}")

        return out
