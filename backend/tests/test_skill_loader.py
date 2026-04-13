"""Skill loader fallback tests."""

import importlib.util
from pathlib import Path
import sys

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LOADER_PATH = BACKEND_ROOT / "agent" / "skill_runtime" / "loader.py"
LOADER_SPEC = importlib.util.spec_from_file_location("skill_loader_module", LOADER_PATH)
if LOADER_SPEC is None or LOADER_SPEC.loader is None:
    raise RuntimeError(f"Failed to load skill loader module from {LOADER_PATH}")
LOADER_MODULE = importlib.util.module_from_spec(LOADER_SPEC)
sys.modules[LOADER_SPEC.name] = LOADER_MODULE
LOADER_SPEC.loader.exec_module(LOADER_MODULE)
SkillLoader = LOADER_MODULE.SkillLoader


@pytest.mark.parametrize(
    ("reference_path", "expected_name"),
    [
        ("references/dimensions/organic.md", "texture.md"),
        ("references/dimensions/technical.md", "typography.md"),
        ("references/dimensions/balanced.md", "density.md"),
    ],
)
def test_dimension_aliases_resolve_to_canonical_reference_files(
    reference_path: str,
    expected_name: str,
) -> None:
    """Dimension option aliases should resolve to existing reference files."""
    loader = SkillLoader(workspace=BACKEND_ROOT)
    skill = loader.get_skill("baoyu-slide-deck")

    assert skill is not None

    resolved = loader.resolve_reference_path(skill, reference_path)

    assert resolved.name == expected_name
    assert resolved.exists()
