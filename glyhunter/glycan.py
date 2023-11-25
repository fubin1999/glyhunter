from __future__ import annotations

from collections.abc import Mapping, Generator, Iterable
from itertools import product

from attr import frozen, field, define

MONOSACCHARIDES = [
    "Hex",
    "HexNAc",
    "dHex",
    "Pen",
    "NeuAc",
    "NeuGc",
    "KDN",
    "HexA",
    "Ac",  # global modification
    "P",  # global modification
    "S",  # global modification
]
"""All monosaccharides supported by GlyHunter. 

All notations are in Byonic format, e.g. dHex for deoxyhexose (not Fuc).
The order is important, as it is used to sort the monosaccharides in the output.
Note that global modifications are also listed here, e.g. Ac for acetylation,
as they are treated as monosaccharides in GlyHunter.
"""

MASSES = {
    "Hex": 162.0528,
    "HexNAc": 203.0794,
    "dHex": 146.0579,
    "Pen": 132.0423,
    "NeuAc": 291.0954,
    "NeuGc": 307.0903,
    "KDN": 250.0689,
    "HexA": 176.0321,
    "H+": 1.0073,
    "H20": 18.0106,
    "K+": 38.9637,
    "Na+": 22.9898,
    "Ac": 42.0106,
    "P": 79.9663,
    "S": 79.9568,
}


def generate_ion(
    comp: Mapping[str, int],
    reducing_end: float,
    charge_carrier: str,
    modifications: Mapping[str, list[float]],
    global_mod_constraints: Mapping[str, int],
) -> Generator[Ion, None, None]:
    """Generate all possible ions from a composition and possible modifications.

    All possible combinations of modifications will be used.

    For example, if `modifications` are `{"NeuAc": [0.0, 1.0]}`,
    and the composition is "HexNAc(2)Hex(5)NeuAc(2)",
    then all possible ions are:
        - "HexNAc(2)Hex(5)NeuAc(2)"
        - "HexNAc(2)Hex(5)NeuAc(1)NeuAc[+1.0000](1)"
        - "HexNAc(2)Hex(5)NeuAc[+1.0000](2)"

    Args:
        comp: The composition of the glycan, with monosaccharide names
            as keys and their counts as values.
        reducing_end: The mass of the reducing end modification.
        charge_carrier: The charge carrier to use.
        modifications: The modifications to use. The keys are the monosaccharide names,
            and the values are the mass of the modifications.
        global_mod_constraints: The constraints of global modifications, with
            global modification names as keys and their max counts as values.
    """
    modifications = {k: modifications.get(k, [0.0]) for k in comp}
    for mods in product(*modifications.values()):
        comp_with_mods = {
            MonoSaccharide(name, modi): comp[name]
            for name, modi in zip(modifications, mods)
        }
        for global_mods in _possible_global_modifications(global_mod_constraints):
            comp_with_global_mods = comp_with_mods.copy()
            for name, count in global_mods.items():
                comp_with_global_mods[MonoSaccharide(name)] = count
            yield Ion(
                comp=comp_with_global_mods,
                reducing_end=reducing_end,
                charge_carrier=charge_carrier,
            )


def _possible_global_modifications(
    constraints: Mapping[str, int]
) -> Generator[dict[str, int], None, None]:
    """Generate all possible global modifications.

    Args:
        constraints: The constraints of the glycan, with monosaccharide names
            as keys and their max counts as values.

    Yields:
        dict: A possible global modification.
    """
    for mods in product(*[range(constraints[k] + 1) for k in constraints]):
        yield {k: v for k, v in zip(constraints, mods) if v != 0}


def check_comp(comp: dict[str, int]) -> tuple[bool, str]:
    """Check the validity of a composition.

    Args:
        comp: The composition to check, with monosaccharide names
            as keys and their counts as values.

    Returns:
        bool: Whether the composition is valid.
        str: The reason of not being valid.
            If valid, it is an empty string.
    """
    invalid_names = set(comp) - set(MONOSACCHARIDES)
    if invalid_names:
        return False, f"Unknown monosaccharides: {', '.join(sorted(invalid_names))}."
    return True, ""


@frozen
class MonoSaccharide:
    """A monosaccharide.

    Attributes:
        name (str): The name of the monosaccharide.
        modi (float): The mass of the modification.
    """

    name: str = field()
    modi: float = field(default=0.0)

    @name.validator
    def _validate_name(self, attribute, value):
        if value not in MONOSACCHARIDES:
            raise ValueError(f"Unknown monosaccharide {value}.")

    def __str__(self):
        if self.modi == 0.0:
            return self.name
        return f"{self.name}[{self.modi:+.4f}]"

    @property
    def mass(self) -> float:
        """The mass of the monosaccharide."""
        return MASSES[self.name] + self.modi


@define
class Ion:
    """An ion of a glycan.

    Attributes:
        comp (Mapping): The composition of the glycan, with MonoSaccharides as keys and
            their counts as values.
        reducing_end (float): The mass of the reducing end modification.
        charge_carrier (str): The charge carrier to use. Default to "Na+".
    """

    comp: dict[MonoSaccharide, int] = field(converter=dict)
    reducing_end: float = field(default=0.0)
    charge_carrier: str = field(default="Na+")

    def __attrs_post_init__(self):
        # Sort the monosaccharides by their name
        # Note that dict in python is ordered since 3.7
        self.comp = {
            k: self.comp[k]
            for k in sorted(self.comp, key=lambda x: MONOSACCHARIDES.index(x.name))
        }

    def __str__(self):
        return "".join([f"{k}({v})" for k, v in self.comp.items()])

    @property
    def mz(self) -> float:
        """The mass of the glycan composition."""
        return (
            sum(k.mass * v for k, v in self.comp.items())
            + self.reducing_end
            + MASSES["H20"]
            + MASSES[self.charge_carrier]
        )

    @classmethod
    def from_tuples(
        cls,
        comp_tuples: Iterable[tuple[str, float, int]],
        reducing_end: float,
        charge_carrier: str,
    ) -> Ion:
        """Helper method for fast creation of an Ion object.

        Args:
            comp_tuples: An iterable of tuples, each of which contains
                the name, modification, and count of a monosaccharide.
            reducing_end: The mass of the reducing end modification.
            charge_carrier: The charge carrier to use.

        Examples:
            >>> Ion.from_tuples([("A", 0.0, 1), ("B", 1.0, 2)])
        """
        comp = {MonoSaccharide(name, modi): count for name, modi, count in comp_tuples}
        return cls(comp, reducing_end, charge_carrier)
