import os, openai, logging

openai.api_key = os.getenv("OPENAI_API_KEY", "")
PREMIUM_MODEL = os.getenv("OPENAI_PREMIUM_MODEL", "gpt-4.1")

class GPT41:
    MODEL = PREMIUM_MODEL
    PRICE_IN  = 0.002   # $ per 1k input tokens
    PRICE_OUT = 0.008   # $ per 1k output tokens

    def chat(self, prompt: str) -> str:
        resp = openai.ChatCompletion.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            timeout=20,
        )
        cost = (resp.usage.prompt_tokens/1000)*self.PRICE_IN + \
               (resp.usage.completion_tokens/1000)*self.PRICE_OUT
        logging.getLogger("emaillm").info("OpenAI cost $%.4f", cost)
        return resp.choices[0].message.content.strip()
