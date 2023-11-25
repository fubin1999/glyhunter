from functools import partial

import pytest
from attrs import define

from glyhunter.denovo import DeNovoEngine
from glyhunter.glycan import MonoSaccharide, Ion


class TestDeNovoEngine:
    @pytest.mark.parametrize(
        "target, solutions",
        [
            (3, [[0, 0, 0], [0, 1], [2]]),
            (4, [[0, 0, 0, 0], [0, 0, 1], [0, 2], [1, 1]]),
            (0, [[]]),
            (1.5, []),
        ],
        ids=[f"target={t}" for t in (3, 4, 0, 1.5)],
    )
    def test_backtrack_algorithm(self, target, solutions):
        """Test the algorithm of `DeNovoEngine._combination_sum`."""
        tol = 0.1
        candidates = [1, 2, 3]
        assert DeNovoEngine._combination_sum(target, tol, candidates) == solutions

    def test_get_mono_candidates(self):
        modifications = {"A": [1.0], "B": [2.0, 3.0]}
        assert DeNovoEngine._get_mono_candidates(modifications) == [
            MonoSaccharide("A", 1.0),
            MonoSaccharide("B", 2.0),
            MonoSaccharide("B", 3.0),
        ]

    def test_filter_constraints(self):
        def mono(name, modi):
            """Helper function to create a MonoSaccharide."""
            return MonoSaccharide(name, modi)

        constraints = {"A": (1, 2), "B": (2, 3)}
        comps = [
            {mono("A", 0.0): 1, mono("B", 0.0): 2},  # kept (A1B2)
            {mono("A", 0.0): 2, mono("B", 0.0): 3},  # kept (A2B3)
            {mono("A", 0.0): 0, mono("B", 0.0): 2},  # filtered (B2)
            {mono("A", 0.0): 1, mono("B", 0.0): 1},  # filtered (A1B1)
            {mono("A", 0.0): 2, mono("B", 0.0): 4},  # filtered (A2B4)
            {
                mono("A", 0.0): 1,
                mono("A", 1.0): 2,
                mono("B", 0.0): 2,
            },  # filtered (A3B2)
        ]
        result = DeNovoEngine._filter_constrains(comps, constraints)
        expected = [
            {mono("A", 0.0): 1, mono("B", 0.0): 2},
            {mono("A", 0.0): 2, mono("B", 0.0): 3},
        ]
        assert result == expected

    @pytest.fixture
    def denovo(self):
        return DeNovoEngine(
            charge_carrier="Na+",
            reducing_end=1.0,
            modifications={"A": [0.0, 1.0], "B": [0.0]},
            constraints={"A": (0, 2), "B": (0, 2)},
        )
        # Monosaccharides: A: 1.0, A[+1.0]: 2.0, B: 2.0

    @pytest.mark.parametrize(
        "target, expected",
        [
            (13, [[("A", 0.0, 1)]]),
            (14, [[("A", 0.0, 2)], [("A", 1.0, 1)], [("B", 0.0, 1)]]),
            (15, [[("A", 0.0, 1), ("B", 0.0, 1)], [("A", 0.0, 1), ("A", 1.0, 1)]]),
        ],
        ids=[f"target={t}" for t in (13, 14, 15)],
    )
    def test_search(self, denovo, target, expected):
        make_ion = partial(Ion.from_tuples, reducing_end=1.0, charge_carrier="Na+")
        # H20: 10, reducing end: 1, Na+: 1
        result = denovo.search(target, tol=0.1)
        expected = [make_ion(ion) for ion in expected]

        assert len(result) == len(expected)
        assert compare_ion_lists(result, expected)

    def test_search_closest(self, mocker, denovo):
        @define
        class MockIon:
            mz: float

        ion_list = [MockIon(mz) for mz in (2., 1., 3.)]
        mocker.patch("glyhunter.denovo.DeNovoEngine.search", return_value=ion_list)

        result = denovo.search_closest(1.1, tol=0.1)
        assert result == MockIon(1.)

    def test_search_closest_empty(self, mocker, denovo):
        mocker.patch("glyhunter.denovo.DeNovoEngine.search", return_value=[])
        result = denovo.search_closest(1.1, tol=0.1)
        assert result is None


def compare_ion_lists(list1, list2):
    """Helper function to compare two lists of ions.

    The order of the two lists does not matter.
    """
    for ion1 in list1:
        matched = False
        for ion2 in list2:
            if ion1 == ion2:
                matched = True
                break
        if not matched:
            return False
    return True


def test_compare_ion_lists():
    l1 = [Ion.from_tuples([("A", 0.0, 1), ("B", 0.0, 2)], 1.0, "Na+")]
    l2 = [Ion.from_tuples([("B", 0.0, 2), ("A", 0.0, 1)], 1.0, "Na+")]
    assert compare_ion_lists(l1, l2)