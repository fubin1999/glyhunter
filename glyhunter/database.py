"""This module implements the database for GlyHunter."""
from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Optional

from attrs import define, field

from glyhunter import utils
from glyhunter.glycan import Ion, generate_ion, check_comp


def load_database(
    filepath: Optional[str | Path] = None,
    *,
    charge_carrier: str,
    reducing_end: float,
    modifications: Mapping[str, list[float]],
    global_mod_constraints: Mapping[str, int],
):
    """Load the database.

    Args:
        filepath: Path to the database file. If None, the default database will be used.
        charge_carrier: The charge carrier to use.
        reducing_end: The mass of the reducing end modification.
        modifications: The modifications to use. The keys are the monosaccharides and
            the values are the mass of the modifications. Optional.
        global_mod_constraints: The constraints of global modifications, with
            global modification names as keys and their max counts as values.

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
        global_mod_constraints=global_mod_constraints,
    )


class DatabaseError(Exception):
    """Base class for all database errors."""


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
        reducing_end: float = 0.0,
        modifications: Optional[Mapping[str, list[float]]] = None,
        global_mod_constraints: Optional[Mapping[str, int]] = None,
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
            reducing_end: The mass of the reducing end modification. Default to 0.0.
            modifications: The modifications to use. The keys are the monosaccharides and
                the values are the mass of the modifications. Optional.
            global_mod_constraints: The constraints of global modifications, with
                global modification names as keys and their max counts as values. Optional.

        Returns:
            Database: The Database object.
        """
        if modifications is None:
            modifications = {}
        if global_mod_constraints is None:
            global_mod_constraints = {}

        ions: list[Ion] = []
        with open(filename, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                comp_str = line.split("%")[0]  # Ignore the mass behind "%"
                comp_dict = _parse_byonic_line(comp_str)
                valid, reason = check_comp(comp_dict)
                if not valid:
                    raise DatabaseError(f"Invalid composition: {comp_str}. {reason}")
                ions.extend(
                    generate_ion(
                        comp_dict,
                        reducing_end,
                        charge_carrier,
                        modifications,
                        global_mod_constraints,
                    )
                )

        return cls(data=ions)


def _parse_byonic_line(line: str) -> dict[str, int]:
    """Parse a line from the Byonic file."""
    comp: dict[str, int] = {}
    for match in re.finditer(r"([A-Za-z]+)\((\d+)\)", line):
        name = match.group(1)
        count = int(match.group(2))
        comp[name] = count
    return comp
