from scrapy_project.framing_llm import LLMFramingAnalyzer

def test_analyze_framing_empty_returns_empty_dict():
    llm = LLMFramingAnalyzer()
    assert llm.analyze_framing("   ") == {}

def test_analyze_framing_nonempty_returns_schema(mocker):
    llm = LLMFramingAnalyzer()
    mocker.spy(llm, "build_prompt")
    out = llm.analyze_framing("texto de prueba")
    # Estructura esperada
    assert set(out.keys()) == {"ideological_frame", "narrative_role", "emotions", "summary"}
    assert set(out["narrative_role"].keys()) == {"actor", "victim", "antagonist"}
    # Se construyó el prompt
    llm.build_prompt.assert_called_once()

def test_build_prompt_truncates_long_text():
    llm = LLMFramingAnalyzer()
    long = "x" * 5000
    prompt = llm.build_prompt(long)
    assert len(prompt) < 3000  # por el límite de 2000 chars del texto
    assert "Texto a analizar" in prompt
