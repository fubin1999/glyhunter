from pathlib import Path

import pytest

from glyhunter.api import initiate


@pytest.fixture
def clean_dir(tmp_path) -> Path:
    """Create a clean directory for testing."""
    dirpath = tmp_path / "clean_dir"
    dirpath.mkdir()
    return dirpath


@pytest.fixture(autouse=True)
def patch_home_path(monkeypatch, clean_dir) -> Path:
    """Patch the home directory to a clean directory."""
    monkeypatch.setattr("glyhunter.api.Path.home", lambda: clean_dir)
    return clean_dir


@pytest.fixture
def glyhunter_init():
    """Initialize GlyHunter."""
    initiate()
