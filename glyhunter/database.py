"""This module implements the database for GlyHunter."""
from __future__ import annotations

import re
from collections.abc import Generator, Mapping, Iterable
from itertools import product
from pathlib import Path
from typing import Optional, Protocol

from attrs import define, frozen, field

from glyhunter import utils

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
    "P": 79.9663,
    "S": 79.9568,
}

MONOSACCHARIDES = ["Hex", "HexNAc", "dHex", "Pen", "NeuAc", "NeuGc", "KDN", "HexA"]
"""All monosaccharides supported by GlyHunter. 
All notations are in Byonic format, e.g. dHex for deoxyhexose (not Fuc).
The order is important, as it is used to sort the monosaccharides in the output."""


def load_database(
    filepath: Optional[str | Path] = None,
    *,
    charge_carrier: str,
    reducing_end: float,
    modifications: Mapping[str, list[float]],
):
    """Load the database.

    Args:
        filepath: Path to the database file. If None, the default database will be used.
        charge_carrier: The charge carrier to use.
        reducing_end: The mass of the reducing end modification.
        modifications: The modifications to use. The keys are the monosaccharides and
            the values are the mass of the modifications. Optional.

    Returns:
        Database: The database.
    """
    if filepath is None:
        filepath = utils.get_db_path()
    return Database.from_byonic(
        filepath,
        charge_carrier=charge_carrier,
        reducing_end=reducing_end,
        modifications=modifications,
    )


class DatabaseError(Exception):
    """Base class for all database errors."""


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
class Composition:
    """A glycan composition.

    Attributes:
        comp (Mapping): The composition of the glycan, with MonoSaccharides as keys and
            their counts as values.
        reducing_end (float): The mass of the reducing end modification.
    """

    comp: dict[MonoSaccharide, int] = field(converter=dict)
    reducing_end: float = field(default=0.0)

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
    def mass(self) -> float:
        """The mass of the glycan composition."""
        return (
            sum(k.mass * v for k, v in self.comp.items())
            + self.reducing_end
            + MASSES["H20"]
        )


@define
class Ion:
    """An ion of a glycan."""

    comp: Composition
    charge: int = 1
    charge_carrier: str = "Na+"

    @property
    def mz(self) -> float:
        """m/z value of the ion."""
        return self.comp.mass / self.charge + MASSES[self.charge_carrier]


class SupportSearch(Protocol):
    """Protocol for supporting search."""

    def search(self, mz: float, tol: float) -> list[Ion]:
        ...

    def search_closest(self, mz: float, tol: float) -> Ion | None:
        ...


@define
class Database:
    """A database of glycan compositions.

    This database could be built from a Byonic file.
    See `Database.from_byonic_file` for more details.
    """

    data: list[Ion] = field(factory=list, repr=False)

    def search(self, mz: float, tol: float) -> list[Ion]:
        """Search the database for ion matching the given m/z and tolerance.

        The result is sorted by the difference between the m/z and the given m/z.
        The first element is the closest ion.

        Args:
            mz (float): The m/z to search for.
            tol (float): The tolerance to use.

        Returns:
            list[Ion]: The matching ions.
        """
        result = [c for c in self.data if abs(c.mz - mz) <= tol]
        return sorted(result, key=lambda c: abs(c.mz - mz))

    def search_closest(self, mz: float, tol: float) -> Ion | None:
        """Search the database for the ion with the closest m/z to the given m/z.

        Args:
            mz (float): The m/z to search for.
            tol (float): The tolerance to use.

        Returns:
            Ion | None: The closest ion, or None if no ion was found.
        """
        if result := self.search(mz, tol):
            return result[0]
        return None

    @classmethod
    def from_byonic(
        cls,
        filename: str | Path,
        *,
        charge_carrier: str = "Na+",
        charges: Iterable[int] = (1,),
        reducing_end: float = 0.0,
        modifications: Optional[Mapping[str, list[float]]] = None,
    ) -> Database:
        """Build a Database from a Byonic file.

        The `file` is a TXT or BYONIC file with each line containing a glycan composition.
        One example line of the file is "HexNAc(4)Hex(5)dHex(1)NeuAc(1) % 2077.74549812".
        The mass behind "%" is ignored, as GlyHunter will calculate the mass itself.

        The `modifications` argument is a dictionary with the keys being the monosaccharides
        and the values being the masses of the modifications.
        All compositions will be duplicated for each modification,
        with all the combinations of modifications.

        For example, if `modifications` are `{"NeuAc": [0.0, 1.0]}`,
        then all compositions containing NeuAc will be duplicated.
        More concretely, "HexNAc(2)Hex(5)NeuAc(2)" will be duplicated into three compositions:
        "HexNAc(2)Hex(5)NeuAc(2)", "HexNAc(2)Hex(5)NeuAc(1)NeuAc[+1.0000](1)",
        and "HexNAc(2)Hex(5)NeuAc[+1.0000](2)".
        Note that modification being 0.0 means no modification.

        Another example is `{"NeuAc": [1.0]}`,
        which will result in only one composition: "HexNAc(2)Hex(5)NeuAc[+1.0000](2)".

        Args:
            filename: The filename of the Byonic file.
            charge_carrier: The charge carrier to use. Default to "H+".
            charges: The charges to use. Default to 1.
            reducing_end: The mass of the reducing end modification. Default to 0.0.
            modifications: The modifications to use. The keys are the monosaccharides and
                the values are the mass of the modifications. Optional.

        Returns:
            Database: The Database object.
        """
        if modifications is None:
            modifications = {}

        def parse_line(
            line_: str, modifications_: Mapping[str, list[float]]
        ) -> Generator[Composition, None, None]:
            """Parse a line from the Byonic file."""
            # Ignore the mass behind "%"
            line_ = line_.split("%")[0]

            # --- Parse the composition ---
            comp_name_dict: dict[str, int] = {}
            for match in re.finditer(r"([A-Za-z]+)\((\d+)\)", line_):
                name = match.group(1)
                count = int(match.group(2))
                comp_name_dict[name] = count

            # --- Add the modifications ---
            # Get the subset of the modifications that are in the composition,
            # and set the default value to 0.0,
            # The order of modifications is the same as the order of monosaccharides
            # in the composition.
            modifications_ = {k: modifications_.get(k, [0.0]) for k in comp_name_dict}
            # Get all combinations of modifications.
            for mods in product(*modifications_.values()):
                comp_dict = {
                    MonoSaccharide(name, modi): comp_name_dict[name]
                    for name, modi in zip(modifications_, mods)
                }
                yield Composition(comp=comp_dict, reducing_end=reducing_end)

        compositions: list[Composition] = []
        with open(filename, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                compositions.extend(parse_line(line, modifications))

        ions: list[Ion] = []
        for comp in compositions:
            for charge in charges:
                ions.append(
                    Ion(comp=comp, charge=charge, charge_carrier=charge_carrier)
                )

        return cls(data=ions)
