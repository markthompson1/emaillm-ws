import os
import json
from typing import Optional

def load_prompt_templates():
    path = os.path.join(os.path.dirname(__file__), "templates/prompt_templates.json")
    with open(path, "r") as f:
        return json.load(f)

def enhance_prompt(alias_topic: str, subject: Optional[str], body: Optional[str]) -> str:
    templates = load_prompt_templates()
    user_text = (subject or "").strip() + " " + (body or "").strip()
    user_text = user_text.strip()
    word_count = len(user_text.split()) if user_text else 0
    # Map alias_topic to category
    topic_category = alias_to_category(alias_topic)
    if not user_text or word_count <= 4:
        template = templates.get(topic_category)
        if template:
            return template.replace("{topic}", alias_topic)
        else:
            return f"No template for {alias_topic}"
    return user_text

def alias_to_category(alias_topic: str) -> str:
    # Simple mapping for demo: manutd, lakers, etc. → sports
    sports = {"manutd", "lakers", "arsenal", "yankees"}
    finance = {"aapl", "tsla", "msft", "finance", "stocks"}
    weather = {"weather", "london", "nyc", "forecast"}
    t = alias_topic.lower()
    if t in sports:
        return "sports"
    if t in finance:
        return "finance"
    if t in weather:
        return "weather"
    return "sports"  # default fallback
