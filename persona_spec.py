"""
Persona batch entries and display names for parameterized (templated) personas.

Config `personas` entries may be:
  - a string: filename or path (e.g. "passive_ideation.json")
  - an object: { "persona": "file.json", "variables": { "k": "v" }, "id": "optional_suffix" }
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional


class PersonaRunSpec(NamedTuple):
    """One runnable persona: source file, optional {{placeholder}} values, optional short id for labels."""

    file: str
    variables: Dict[str, str]
    instance_id: Optional[str] = None


def normalize_persona_config_entry(entry: Any) -> PersonaRunSpec:
    """Parse one entry from batch_config.json `personas` list. Raises ValueError on bad shape."""
    if isinstance(entry, str):
        s = entry.strip()
        if not s:
            raise ValueError("Empty persona string in config")
        return PersonaRunSpec(s, {}, None)
    if isinstance(entry, dict):
        file_key = entry.get("persona") or entry.get("file")
        if not file_key or not isinstance(file_key, str):
            raise ValueError("Persona object entry must include string 'persona' or 'file'")
        vars_raw = entry.get("variables") or {}
        if not isinstance(vars_raw, dict):
            raise ValueError("Persona 'variables' must be a JSON object")
        variables = {str(k): str(v) for k, v in vars_raw.items()}
        iid = entry.get("id") or entry.get("instance_id")
        iid_str: Optional[str]
        if iid is None or (isinstance(iid, str) and not iid.strip()):
            iid_str = None
        else:
            iid_str = str(iid).strip()
        return PersonaRunSpec(str(file_key).strip(), variables, iid_str)
    raise ValueError(f"Invalid persona entry type: {type(entry).__name__}")


def merge_cli_vars_into_specs(specs: List[PersonaRunSpec], cli_vars: Optional[Dict[str, str]]) -> List[PersonaRunSpec]:
    """Merge CLI --persona-var KEY=VALUE into each spec (CLI overrides per-instance variables)."""
    if not cli_vars:
        return specs
    out: List[PersonaRunSpec] = []
    for s in specs:
        merged = {**s.variables, **cli_vars}
        out.append(PersonaRunSpec(s.file, merged, s.instance_id))
    return out


def display_name_for_spec(spec: PersonaRunSpec) -> str:
    """Human- and filename-safe label for results (stem, optional __id or __k=v...)."""
    stem = Path(spec.file).stem
    if spec.instance_id:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in spec.instance_id)[:80]
        return f"{stem}__{safe}"
    if spec.variables:
        parts: List[str] = []
        for k, v in sorted(spec.variables.items()):
            sv = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(v))[:40]
            parts.append(f"{k}={sv}")
        joined = "_".join(parts)
        return f"{stem}__{joined}"[:200]
    return stem


def spec_sort_key(spec: PersonaRunSpec) -> tuple:
    return (spec.file.lower(), sorted(spec.variables.items()), spec.instance_id or "")
