"""Tests for config.yaml path resolution (installed wheel / Docker)."""

from pathlib import Path

from notebooklm_shared import config as cfg_mod


def test_config_yaml_path_uses_cwd_when_repo_yaml_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Docker: package in site-packages has no config; mount at WORKDIR."""
    cwd_yaml = tmp_path / "config.yaml"
    cwd_yaml.write_text("config_version: 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOTEBOOKLM_CONFIG_PATH", raising=False)

    def fake_repo_root() -> Path:
        return tmp_path / "no_such_repo"

    monkeypatch.setattr(cfg_mod, "_repo_root", fake_repo_root)
    assert cfg_mod._config_yaml_path() == cwd_yaml
