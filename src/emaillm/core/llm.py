# cache wrapper
from emaillm.core.cache import get_or_set
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

    def _call(_):  # compute_fn arg ignored
        return provider.chat(prompt)

    reply, hit = get_or_set(prompt, _call)
    import logging
    logging.getLogger("emaillm").info("cache_%s", "hit" if hit else "miss")
    return reply
