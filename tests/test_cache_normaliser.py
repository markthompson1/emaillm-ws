from emaillm.core.cache import _normalise

def test_normalise():
    assert _normalise("  Hello\nWorld  ") == "hello world"
    assert _normalise("HELLO   world") == "hello world"
