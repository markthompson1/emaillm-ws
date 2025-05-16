def call_llm(model: str, payload: dict) -> str:
    """Stub LLM call—returns a canned reply noting the chosen model."""
    return (f"Hi,\n\n"
            f"This is a placeholder response generated via the {model} route.\n"
            f"In production, this will call the real LLM API.\n\n"
            f"– EMAILLM MVP")
