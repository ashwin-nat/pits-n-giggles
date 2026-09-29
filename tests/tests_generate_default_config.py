import json
from pathlib import Path

from apps import generate_default_config as gen
from lib.config import PngSettings
from lib.config.io.json import load_config_from_json


def test_writes_valid_default_config(tmp_path: Path):
    out = tmp_path / "cfg.json"
    assert gen.main(str(out)) == gen.EXIT_OK
    assert PngSettings(**json.loads(out.read_text(encoding="utf-8"))) == PngSettings()


def test_defaults_to_png_config_json(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert gen.main() == gen.EXIT_OK
    assert (tmp_path / "png_config.json").is_file()


def test_existing_file_fails_without_force(tmp_path: Path, capsys):
    out = tmp_path / "cfg.json"
    out.write_text("keep me", encoding="utf-8")
    assert gen.main(str(out)) == gen.EXIT_FILE_EXISTS
    assert out.read_text(encoding="utf-8") == "keep me"
    assert "--force" in capsys.readouterr().err


def test_force_overwrites_existing_file(tmp_path: Path):
    out = tmp_path / "cfg.json"
    out.write_text("old", encoding="utf-8")
    assert gen.main(str(out), force=True) == gen.EXIT_OK
    assert "Network" in json.loads(out.read_text(encoding="utf-8"))


def test_generated_file_roundtrips_through_loader(tmp_path: Path):
    out = tmp_path / "cfg.json"
    gen.main(str(out))
    before = out.read_text(encoding="utf-8")
    assert load_config_from_json(str(out), fail_if_missing=True) == PngSettings()
    assert out.read_text(encoding="utf-8") == before  # loader found nothing to repair
