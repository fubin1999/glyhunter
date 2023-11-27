from __future__ import annotations

import collections
from collections.abc import Sequence

from attrs import define, field

from glyhunter import glycan
from glyhunter.glycan import Ion, MonoSaccharide


@define
class DeNovoEngine:
    """A search engine for de novo glycan sequencing.

    This engine uses a backtracking algorithm to find all possible glycan compositions
    that match the given m/z and tolerance.
    The compositions are then filtered by the constraints, i.e. the minimum and maximum
    number of monosaccharides.

    Attributes:
        charge_carrier: The charge carrier to use.
        reducing_end: The mass of the reducing end modification.
        _modifications: The modifications to use. The keys are the monosaccharides and
            the values are the mass of the modifications.
        _mono_constraints: The constraints to use. The keys are the monosaccharides and
            the values are the minimum and maximum number of the monosaccharides.
        _global_mod_constraints: The constraints of global modifications, with
            global modification names as keys and their max counts as values.
    """

    charge_carrier: str
    reducing_end: float

    # The 3 attributes below will be used to construct the _mono_candidates
    # Therefore, there are according getters for them,
    # to make sure that the _mono_candidates is updated when they are changed.
    _modifications: dict[str, list[float]]
    _mono_constraints: dict[str, tuple[int, int]]
    _global_mod_constraints: dict[str, int]

    _mono_candidates: list[MonoSaccharide] = field(init=False, repr=False)
    """This attribute stores all possible monosaccharides with different modifications.
    It is used as the candidates for the de novo search."""
    _constraints: dict[str, tuple[int, int]] = field(init=False, repr=False)
    """This attribute stores the constraints of the monosaccharides and global
    modifications. It is used as the constraints for the de novo search."""

    def __attrs_post_init__(self):
        self._update_mono_candidates()
        self._update_constraints()

    def _update_mono_candidates(self) -> None:
        """Generate all possible monosaccharides with different modifications.

        Both monosaccharides and global modifications (e.g. Ac) are considered.
        """
        monos: list[MonoSaccharide] = []

        # Add monosaccharides
        for name, mods in self._modifications.items():
            if (
                self._mono_constraints[name][1] > 0
            ):  # max count > 0, for speed up searching
                for mod in mods:
                    monos.append(MonoSaccharide(name, mod))

        # Add global modifications
        for name, count in self._global_mod_constraints.items():
            if count > 0:  # same as above
                monos.append(MonoSaccharide(name))

        self._mono_candidates = monos

    def _update_constraints(self) -> None:
        """Generate the constraints of the monosaccharides and global modifications."""
        constraints = {}
        for name, (min_, max_) in self._mono_constraints.items():
            constraints[name] = (min_, max_)
        for name, count in self._global_mod_constraints.items():
            constraints[name] = (0, count)
        self._constraints = constraints

    @property
    def modifications(self) -> dict[str, list[float]]:
        return self._modifications

    @modifications.setter
    def modifications(self, value: dict[str, list[float]]):
        self._modifications = value
        self._update_mono_candidates()

    @property
    def mono_constraints(self) -> dict[str, tuple[int, int]]:
        return self._mono_constraints

    @mono_constraints.setter
    def mono_constraints(self, value: dict[str, tuple[int, int]]):
        self._mono_constraints = value
        self._update_mono_candidates()
        self._update_constraints()

    @property
    def global_mod_constraints(self) -> dict[str, int]:
        return self._global_mod_constraints

    @global_mod_constraints.setter
    def global_mod_constraints(self, value: dict[str, int]):
        self._global_mod_constraints = value
        self._update_mono_candidates()
        self._update_constraints()

    def search(self, mz: float, tol: float) -> list[Ion]:
        """De novo search for ion matching the given m/z and tolerance.

        Args:
            mz (float): The m/z to search for.
            tol (float): The tolerance to use.
        """
        target = (
            mz
            - glycan.MASSES[self.charge_carrier]
            - self.reducing_end
            - glycan.MASSES["H20"]
        )
        candidates = [mono.mass for mono in self._mono_candidates]
        solutions = self._combination_sum(target, tol, candidates)

        comps: list[dict[MonoSaccharide, int]] = []
        for sol in solutions:
            comp = collections.Counter(self._mono_candidates[i] for i in sol)
            comps.append(comp)
        comps = self._filter_constrains(comps, self._constraints)

        ions = [Ion(comp, self.reducing_end, self.charge_carrier) for comp in comps]
        return ions

    @staticmethod
    def _combination_sum(
        target: float, tol: float, candidates: Sequence[float]
    ) -> list[list[int]]:
        """Find all combinations of the candidates that sum to the target within tol.

        This is the core algorithm of the de novo search.
        Candidates can be used multiple times.
        No duplicate combinations are allowed.

        Args:
            target (float): The target sum.
            tol (float): The tolerance.
            candidates (Sequence[float]): The candidates.

        Returns:
            list[list[int]]: The combinations.
        """

        def backtrack(current: float, start: int, path: list[int]):
            if current > target + tol:
                return
            if current >= target - tol:
                solutions.append(path)
                return

            for i in range(start, len(candidates)):
                backtrack(current + candidates[i], i, path + [i])

        solutions: list[list[int]] = []
        backtrack(0.0, 0, [])
        return solutions

    @staticmethod
    def _filter_constrains(
        comps: Sequence[dict[MonoSaccharide, int]],
        constraints: dict[str, tuple[int, int]],
    ):
        """Filter the compositions by the constraints.

        This method will filter the compositions by the constraints (min and max
        number of monosaccharides).
        Modifications are not considered when counting the monosaccharides.
        """
        results: list[dict[MonoSaccharide, int]] = []
        for comp in comps:
            comp_x_modif = collections.Counter()
            for mono, count in comp.items():
                comp_x_modif[mono.name] += count
            for mono, (min_, max_) in constraints.items():
                if comp_x_modif[mono] < min_ or comp_x_modif[mono] > max_:
                    break
            else:
                results.append(comp)
        return results

    def search_closest(self, mz: float, tol: float) -> Ion | None:
        """De novo search for the ion with the closest m/z to the given m/z.

        Args:
            mz (float): The m/z to search for.
            tol (float): The tolerance to use.

        Returns:
            Ion | None: The closest ion, or None if no ion was found.
        """
        if ions := self.search(mz, tol):
            ions.sort(key=lambda x: abs(x.mz - mz))
            return ions[0]
        return None
