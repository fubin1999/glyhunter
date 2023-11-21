import pandas as pd
import pytest
from typing import NamedTuple
from pandas.testing import assert_frame_equal

from glyhunter.search import MassListSearcher
from glyhunter.mass_list import Peak


class MockResult(NamedTuple):
    mz: float
    charge: int
    charge_carrier: str
    comp: str


class MockSearcher:

    def search(self, mz, tol):
        return [MockResult(mz, 1, "Na+", "HexNAc(2)Hex(5)NeuAc(1)")]

    def search_closest(self, mz, tol):
        return MockResult(mz, 1, "Na+", "HexNAc(2)Hex(5)NeuAc(1)")


@pytest.fixture
def searcher():
    searcher = MockSearcher()
    return MassListSearcher(searcher, mz_tol=10, all_candidates=False)


@pytest.fixture
def searcher_all_candi():
    searcher = MockSearcher()
    return MassListSearcher(searcher, mz_tol=10, all_candidates=True)


def test_run(searcher):
    _test_run(searcher)


def test_run_all_candi(searcher_all_candi):
    _test_run(searcher_all_candi)


def _test_run(searcher):
    mass_list = [Peak(1000., 1001., 1e5, 1e5, 10.)]
    result = searcher.run(mass_list)
    expected_data = {
        "glycan": ["HexNAc(2)Hex(5)NeuAc(1)"],
        "raw_mz": [1000.],
        "calibrated_mz": [1001.],
        "theoretical_mz": [1001.],
        "intensity": [1e5],
        "area": [1e5],
        "sn": [10.],
        "charge_carrier": ["Na+"],
        "ppm": [0.0]
    }
    expected = pd.DataFrame(expected_data)
    assert_frame_equal(result, expected)
