"""Tests for persona batch specs and display names."""
from persona_spec import (
    PersonaRunSpec,
    display_name_for_spec,
    merge_cli_vars_into_specs,
    normalize_persona_config_entry,
    spec_sort_key,
)


def test_normalize_string_entry() -> None:
    s = normalize_persona_config_entry("foo.json")
    assert s == PersonaRunSpec("foo.json", {}, None)


def test_normalize_object_entry() -> None:
    s = normalize_persona_config_entry(
        {"persona": "x.json", "variables": {"a": "1", "b": "2"}, "id": "run1"}
    )
    assert s.file == "x.json"
    assert s.variables == {"a": "1", "b": "2"}
    assert s.instance_id == "run1"


def test_merge_cli_overrides_instance() -> None:
    specs = [PersonaRunSpec("p.json", {"a": "batch"}, None)]
    out = merge_cli_vars_into_specs(specs, {"a": "cli"})
    assert out[0].variables["a"] == "cli"


def test_display_name_stem_only() -> None:
    assert display_name_for_spec(PersonaRunSpec("passive_ideation.json", {}, None)) == "passive_ideation"


def test_display_name_instance_id() -> None:
    d = display_name_for_spec(PersonaRunSpec("p.json", {"x": "y"}, "trial-a"))
    assert d.startswith("p__")
    assert "trial" in d or "trial-a" in d


def test_spec_sort_key_stable() -> None:
    a = PersonaRunSpec("b.json", {"z": "1"}, None)
    b = PersonaRunSpec("a.json", {}, None)
    assert spec_sort_key(a) != spec_sort_key(b)
