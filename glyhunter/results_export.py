from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pandas as pd


def write_mass_list_results(
    results: Iterable[tuple[str, pd.DataFrame]], dirpath: str | Path
) -> None:
    """Write mass list results to a directory.

    This function writes the results of a mass list search to a directory,
    with one CSV file per mass list.

    Args:
        results: A list of tuples, each containing the name of the mass list
            and the search results.
        dirpath: Path to the directory to write the results to.
    """
    for name, result_df in results:
        result_df.to_csv(Path(dirpath) / (name + ".csv"), index=False)


def write_summary_tables(
    results: Iterable[tuple[str, pd.DataFrame]], dirpath: str | Path
) -> None:
    """Write summary tables to a directory.

    This functions writes three summary tables to a directory,
    one for each of the following:

    - intensity
    - area
    - signal-to-noise ratio

    Args:
        results: A list of tuples, each containing the name of the mass list
            and the search results.
        dirpath: Path to the directory to write the results to.
    """
    summary_by = ("intensity", "area", "sn")
    for by in summary_by:
        summary_s = [result_df.set_index("glycan")[by] for _, result_df in results]
        summary_df = pd.concat(summary_s, axis=1)
        summary_df.columns = cast(pd.Index, [name for name, _ in results])
        summary_df.to_csv(Path(dirpath) / f"summary_{by}.csv")
