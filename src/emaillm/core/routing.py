def route_email(subject: str, body: str) -> str:
    """Very small rule set matching the spec."""
    text = (subject + " " + body).lower()
    if "google" in text:
        return "Gemini"
    if "excel" in text or "office" in text:
        return "Copilot"
    if "aws" in text or "lambda" in text or "devops" in text:
        return "Titan"
    if "open source" in text or "linux" in text:
        return "Mixtral"
    if "legal" in text or "ethical" in text:
        return "Claude 3"
    if "twitter" in text or "x.com" in text:
        return "Grok"
    return "GPT-4 Turbo"
