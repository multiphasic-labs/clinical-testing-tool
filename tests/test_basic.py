import json
from pathlib import Path


def test_persona_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    passive = root / "personas" / "passive_ideation.json"
    active = root / "personas" / "active_ideation.json"
    mild = root / "personas" / "mild_anxiety.json"
    assert passive.is_file()
    assert active.is_file()
    assert mild.is_file()


def test_batch_config_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "personas" / "batch_config.json"
    assert config_path.is_file()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(data.get("personas"), list)
    assert "passive_ideation.json" in data["personas"]

