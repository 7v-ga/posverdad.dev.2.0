# scrapy_project/heuristics_entities.py
SPANISH_STOP_ENTS = {
    "además", "sin embargo", "no obstante", "también", "hoy", "ayer", "mañana"
}

BAD_POS = {"ADV","SCONJ","CCONJ","DET","PRON"}  # filtro POS simple

def clean_and_unify_entities(ents, spacy_doc=None):
    """
    ents: [{"text": "...", "label": "PER/ORG/LOC/..."}]
    - Remueve blocklist lingüística básica (ej. "además").
    - Si en el mismo artículo hay "Nombre Apellido" (PER) y también "Apellido", mapea "Apellido" al nombre completo,
      solo si hay un único candidato de nombre completo con ese apellido.
    - Deduplica (texto+label).
    """
    # 1) limpiar términos triviales
    filtered = []
    for ent in ents:
        text = (ent.get("text") or "").strip()
        label = (ent.get("label") or "").strip()
        if not text or len(text) == 1:
            continue
        low = text.lower()
        if low in SPANISH_STOP_ENTS:
            continue

        if spacy_doc is not None:
            # Filtro POS heurístico: si todos los tokens coincidentes son "funcionales", descartamos
            toks = [t for t in spacy_doc if t.text == text]
            if toks and all(getattr(t, "pos_", "") in BAD_POS for t in toks):
                continue

        filtered.append({"text": text, "label": label})

    # 2) unificar apellidos -> nombre completo (solo PER)
    persons = [e["text"] for e in filtered if e.get("label") == "PER"]
    fullnames = [p for p in persons if " " in p]
    last_to_full = {}
    for fn in fullnames:
        last = fn.split()[-1]
        last_to_full.setdefault(last, set()).add(fn)

    unified = []
    for e in filtered:
        if e.get("label") == "PER" and " " not in e["text"]:
            last = e["text"]
            cands = last_to_full.get(last, set())
            if len(cands) == 1:
                e = {"text": list(cands)[0], "label": "PER"}
        unified.append(e)

    # 3) deduplicar
    seen, out = set(), []
    for e in unified:
        key = (e["text"], e["label"])
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out
