import pytest
from emaillm.nlp.prompt_enhancer import enhance_prompt

def test_blank_email_to_manutd_returns_sports_template():
    result = enhance_prompt("manutd", subject=None, body=None)
    assert "Summarise the latest news" in result
    assert "manutd" in result

def test_long_body_returns_body_unchanged():
    body = "This is a long body with more than four words."
    result = enhance_prompt("manutd", subject=None, body=body)
    assert result == body
