from collections.abc import Iterable
from typing import NamedTuple

import pandas as pd
from attrs import define

from .database import SupportSearch
from .mass_list import MassList


def search_one(
    mass_list: MassList,
    search_engine: SupportSearch,
    mz_tol: float,
    *,
    all_candidates: bool = False,
) -> pd.DataFrame:
    """Search one peak.

    Args:
        mass_list: A list of m/z and intensity pairs.
        search_engine: An object supporting `search` method.
        mz_tol: The m/z tolerance to use for the search, in ppm.
        all_candidates: Whether to return all candidates or only the best one.
            Default: False.

    Returns:
        pd.DataFrame: A dataframe with the results.
    """
    searcher = MassListSearcher(search_engine, mz_tol, all_candidates)
    return searcher.run(mass_list)


def search_many(
    mass_lists: Iterable[MassList],
    search_engine: SupportSearch,
    mz_tol: float,
    *,
    all_candidates: bool = False,
) -> list[tuple[str, pd.DataFrame]]:
    """Search many peaks.

    Args:
        mass_lists: A list of MassList objects.
        search_engine: An object supporting `search` method.
        mz_tol: The m/z tolerance to use for the search, in ppm.
        all_candidates: Whether to return all candidates or only the best one.
            Default: False.

    Returns:
        list[tuple[str, pd.DataFrame]]: A list of tuples, each containing the name
            of the mass list and the search results.
    """
    searcher = MassListSearcher(search_engine, mz_tol, all_candidates)
    results: list[tuple[str, pd.DataFrame]] = []
    for mass_list in mass_lists:
        result = searcher.run(mass_list)
        results.append((mass_list.name, result))
    return results


@define
class MassListSearcher:
    """The main class for searching the spectra.

    Attributes:
        search_engine: An object supporting `search` method.
        mz_tol: The m/z tolerance to use for the search, in ppm.
        all_candidates: Whether to return all candidates or only the best one.
            Default: False.
    """

    search_engine: SupportSearch
    mz_tol: float
    all_candidates: bool = False

    def run(self, mass_list: MassList) -> pd.DataFrame:
        """Run GlyHunter on a list of m/z and intensity pairs.

        Args:
            mass_list: A list of m/z and intensity pairs.

        Returns:
            pd.DataFrame: A dataframe with the results.
        """
        results = []
        for peak in mass_list:
            tol = peak.mz * self.mz_tol / 1e6
            if self.all_candidates:
                # This mode is for when we want to return all candidates
                # within the tolerance.
                raise NotImplementedError
            else:
                if result := self.search_engine.search_closest(peak.mz, tol):
                    record = SearchRecord(
                        glycan=str(result.comp),
                        raw_mz=peak.raw_mz,
                        calibrated_mz=peak.calibrated_mz,
                        theoretical_mz=result.mz,
                        intensity=peak.intensity,
                        area=peak.area,
                        sn=peak.sn,
                        charge=result.charge,
                        charge_carrier=result.charge_carrier,
                    )
                    results.append(record)
        result_df = pd.DataFrame(results, columns=SearchRecord._fields)

        # Add additional columns
        result_df["ppm"] = (
            (result_df.calibrated_mz - result_df.theoretical_mz)
            / result_df.raw_mz
            * 1e6
        )
        result_df["ppm"] = result_df["ppm"].round(2)

        return result_df


class SearchRecord(NamedTuple):
    """A record of a search result for a peak."""

    glycan: str
    raw_mz: float
    calibrated_mz: float
    theoretical_mz: float
    intensity: float
    area: float
    sn: float
    charge: int
    charge_carrier: str
