from src.config import deep_merge, load_config


def test_deep_merge_simple():
    a = {"x": 1, "y": {"a": 2}}
    b = {"y": {"b": 3}, "z": 4}
    out = deep_merge(a, b)
    assert out == {"x": 1, "y": {"a": 2, "b": 3}, "z": 4}


def test_deep_merge_overwrite():
    a = {"k": 1}
    b = {"k": 2}
    assert deep_merge(a, b) == {"k": 2}


def test_load_default():
    cfg = load_config("default")
    assert "llm" in cfg
    assert "agents" in cfg


def test_load_strict():
    cfg = load_config("budget_strict")
    assert cfg["defaults"]["pace"] == "relaxed"
