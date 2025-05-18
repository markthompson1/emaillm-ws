from emaillm.core.providers import GPT41

# Map routing strings to provider instances
PROVIDERS = {
    "GPT-4-class": GPT41(),
    "GPT-4.1":     GPT41(),
    "GPT-4 Turbo": GPT41(),   # legacy router string
}

def call_llm(model: str, payload: dict) -> str:
    """Return the provider’s real GPT-4.1 reply text."""
    prompt = payload.get("text") or payload.get("subject", "")
    provider = PROVIDERS.get(model) or PROVIDERS["GPT-4.1"]
    return provider.chat(prompt)
