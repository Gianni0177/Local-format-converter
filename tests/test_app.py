import builtins
import importlib.util
import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app import app, parse_content


def test_index_route_returns_ok():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200


def test_parse_toml_content():
    parsed = parse_content('title = "Format Forge"', "toml")

    assert parsed == {"title": "Format Forge"}


def test_app_import_falls_back_to_tomli(monkeypatch):
    real_import = builtins.__import__
    fake_tomli = types.SimpleNamespace(loads=lambda text: {"fallback": text})

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "tomllib":
            raise ModuleNotFoundError("No module named 'tomllib'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setitem(sys.modules, "tomli", fake_tomli)

    spec = importlib.util.spec_from_file_location(
        "app_with_tomli_fallback",
        "/home/runner/work/Local-format-converter/Local-format-converter/app.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module

    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.parse_content("value = 1", "toml") == {"fallback": "value = 1"}
