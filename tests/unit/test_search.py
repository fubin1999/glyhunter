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

    def search_closest(self, mz, tol):
        pass

    def search_closest(self, mz, tol):
        return MockResult(mz, 1, "Na+", "HexNAc(2)Hex(5)NeuAc(1)")


@pytest.fixture
def glyhunter_instance():
    searcher = MockSearcher()
    return MassListSearcher(searcher, mz_tol=10, all_candidates=False)


def test_run(glyhunter_instance):
    mass_list = [Peak(1000., 1001., 1e5, 1e5, 10.)]
    result = glyhunter_instance.run(mass_list)
    expected_data = {
        "glycan": ["HexNAc(2)Hex(5)NeuAc(1)"],
        "raw_mz": [1000.],
        "calibrated_mz": [1001.],
        "theoretical_mz": [1001.],
        "intensity": [1e5],
        "area": [1e5],
        "sn": [10.],
        "charge": [1],
        "charge_carrier": ["Na+"],
        "ppm": [0.0]
    }
    expected = pd.DataFrame(expected_data)
    assert_frame_equal(result, expected)
