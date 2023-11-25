import pytest


@pytest.fixture(autouse=True)
def simple_masses(monkeypatch):
    monkeypatch.setattr(
        "glyhunter.glycan.MASSES",
        {"A": 1.0, "B": 2.0, "C": 3.0, "Na+": 1.0, "H20": 10.0, "Ac": 1.0},
    )


@pytest.fixture(autouse=True)
def simple_monosaccharides(monkeypatch):
    monkeypatch.setattr("glyhunter.glycan.MONOSACCHARIDES", ["A", "B", "C", "Ac"])
