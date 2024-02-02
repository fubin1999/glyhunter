from collections.abc import Iterable

import pytest

from glyhunter import glycan


class TestMonoSaccharide:
    def test_validate_name(self):
        with pytest.raises(ValueError):
            glycan.MonoSaccharide(name="D")

    def test_str(self):
        assert str(glycan.MonoSaccharide(name="A")) == "A"
        assert str(glycan.MonoSaccharide(name="A", modi=1.0)) == "A[+1.0000]"

    def test_mass(self):
        assert glycan.MonoSaccharide(name="A").mass == 1.0
        assert glycan.MonoSaccharide(name="A", modi=1.0).mass == 2.0


class TestIon:
    @pytest.fixture
    def mono_1(self):
        return glycan.MonoSaccharide(name="A")

    @pytest.fixture
    def mono_2(self):
        return glycan.MonoSaccharide(name="B", modi=1.0)

    def test_mz(self, mono_1, mono_2):
        result = glycan.Ion(
            comp={mono_1: 1, mono_2: 2},
            reducing_end=0.0,
            charge_carrier="Na+",
        )
        assert result.mz == 18.0


class TestGenerateIon:
    @pytest.fixture
    def comp_dict(self):
        return {"A": 1, "B": 2}

    def test_no_modification(self, comp_dict):
        results = list(glycan.generate_ion(comp_dict, 0.0, "Na+", {}, {}))
        assert results == [make_ion([("A", 0.0, 1), ("B", 0.0, 2)])]

    def test_1_modification(self, comp_dict):
        results = list(glycan.generate_ion(comp_dict, 0.0, "Na+", {"A": [1.0]}, {}))
        assert results == [make_ion([("A", 1.0, 1), ("B", 0.0, 2)])]

    def test_2_modifications_on_1_mono(self, comp_dict):
        results = list(
            glycan.generate_ion(comp_dict, 0.0, "Na+", {"A": [1.0, 2.0]}, {})
        )
        assert results == [
            make_ion([("A", 1.0, 1), ("B", 0.0, 2)]),
            make_ion([("A", 2.0, 1), ("B", 0.0, 2)]),
        ]

    def test_2_modifications_on_2_monos(self, comp_dict):
        results = list(
            glycan.generate_ion(comp_dict, 0.0, "Na+", {"A": [1.0], "B": [2.0]}, {})
        )
        assert results == [make_ion([("A", 1.0, 1), ("B", 2.0, 2)])]

    def test_3_modifications_on_2_monos(self, comp_dict):
        results = list(
            glycan.generate_ion(
                comp_dict, 0.0, "Na+", {"A": [1.0], "B": [2.0, 3.0]}, {}
            )
        )
        assert results == [
            make_ion([("A", 1.0, 1), ("B", 2.0, 2)]),
            make_ion([("A", 1.0, 1), ("B", 2.0, 1), ("B", 3.0, 1)]),
            make_ion([("A", 1.0, 1), ("B", 3.0, 2)]),
        ]

    @pytest.mark.parametrize(
        "modifications", [{"A": [1.0], "B": [2.0]}, {"B": [2.0], "A": [1.0]}]
    )
    def test_modification_order(self, comp_dict, modifications):
        """Test the order of keys in the modifications dict does not matter."""
        results = list(glycan.generate_ion(comp_dict, 0.0, "Na+", modifications, {}))
        assert results == [make_ion([("A", 1.0, 1), ("B", 2.0, 2)])]

    def test_reducing_end(self, comp_dict):
        results = list(glycan.generate_ion(comp_dict, 1.0, "Na+", {}, {}))
        assert results == [make_ion([("A", 0.0, 1), ("B", 0.0, 2)], reducing_end=1.0)]

    def test_charge_carrier(self, comp_dict):
        results = list(glycan.generate_ion(comp_dict, 0.0, "K+", {}, {}))
        assert results == [
            make_ion([("A", 0.0, 1), ("B", 0.0, 2)], charge_carrier="K+")
        ]

    def test_global_modifications(self, comp_dict):
        results = list(glycan.generate_ion(comp_dict, 0.0, "Na+", {}, {"Ac": 1}))
        assert results == [
            make_ion([("A", 0.0, 1), ("B", 0.0, 2)]),
            make_ion([("A", 0.0, 1), ("B", 0.0, 2), ("Ac", 0.0, 1)]),
        ]


def test_possible_global_modifications():
    constraints = {"Ac": 1, "P": 1}
    results = list(glycan._possible_global_modifications(constraints))
    assert results == [{}, {"P": 1}, {"Ac": 1}, {"Ac": 1, "P": 1}]


class TestCheckComp:
    def test_valid_comp(self):
        assert glycan.check_comp({"A": 1, "B": 2}) == (True, "")

    @pytest.mark.parametrize(
        "comp, msg",
        [
            ({"B": 1, "D": 2}, "Unknown monosaccharides: D."),
            ({"D": 1, "E": 1}, "Unknown monosaccharides: D, E."),
        ],
    )
    def test_invalid_comp(self, comp, msg):
        assert glycan.check_comp(comp) == (False, msg)


def make_ion(
    comp_tuples: Iterable[tuple[str, float, int]],
    reducing_end: float = 0.0,
    charge_carrier: str = "Na+",
):
    """Helper funtion to make an Ion object."""
    return glycan.Ion.from_tuples(comp_tuples, reducing_end, charge_carrier)
