import numpy as np
import pytest

from glyhunter.mass_list import MassList


class TestMassList:
    def test_from_flex_analysis(self):
        flex_analysis_file = "tests/data/fa_exported.xlsx"
        mass_lists = MassList.from_flex_analysis(flex_analysis_file)
        assert len(mass_lists) == 3
        assert [ml.name for ml in mass_lists] == ["spec1", "spec2", "spec3"]

    @pytest.fixture
    def mass_list(self):
        """Mass list instance for testing."""
        return MassList(
            "test",
            np.array([1, 2, 3]),
            np.array([4, 5, 6]),
            np.array([7, 8, 9]),
            np.array([10, 11, 12]),
        )

    def test_iter(self, mass_list):
        peaks = list(mass_list)
        assert len(peaks) == 3
        assert [peak.mz for peak in peaks] == [1, 2, 3]
        assert [peak.intensity for peak in peaks] == [4, 5, 6]
        assert [peak.area for peak in peaks] == [7, 8, 9]
        assert [peak.sn for peak in peaks] == [10, 11, 12]

    def test_len(self, mass_list):
        assert len(mass_list) == 3

    def test_calibrate(self, mass_list):
        mass_list.calibrate([1.1, 2.1, 3.1], 1e5)
        np.testing.assert_array_almost_equal(mass_list.mz_a, [1.1, 2.1, 3.1])
