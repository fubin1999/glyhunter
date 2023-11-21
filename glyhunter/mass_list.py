from __future__ import annotations

from collections.abc import Iterator, Iterable
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from attrs import define, frozen, field
from numpy.typing import NDArray


@frozen
class Peak:
    """A peak in the mass list."""
    raw_mz: float  # The raw m/z value of the peak.
    calibrated_mz: float | None  # The calibrated m/z value of the peak.
    intensity: float  # The intensity of the peak.
    area: float  # The area of the peak.
    sn: float  # The S/N of the peak.

    @property
    def mz(self) -> float:
        """The m/z value of the peak.

        If the m/z value is calibrated, the calibrated value is returned.
        Otherwise, the raw value is returned.
        """
        return self.calibrated_mz if self.calibrated_mz is not None else self.raw_mz


@define
class MassList:
    """A list of peaks with m/z and intensity values.

    Attributes:
        name: The name of the spectrum.

    Methods:
        from_flex_analysis: Create MassLists from a FlexAnalysis mass list file.
    """

    name: str
    _raw_mz_a: NDArray[np.float64] = field(converter=np.array)
    _intensity_a: NDArray[np.float64] = field(converter=np.array)
    _area_a: NDArray[np.float64] = field(converter=np.array)
    _sn_a: NDArray[np.float64] = field(converter=np.array)
    _calibrated_mz_a: NDArray[np.float64] = field(init=False)

    @property
    def mz_a(self) -> NDArray[np.float64]:
        """The m/z values of the peaks.

        If the m/z values are calibrated, the calibrated values are returned.
        Otherwise, the raw values are returned.
        """
        try:
            return self._calibrated_mz_a
        except AttributeError:
            return self._raw_mz_a

    @classmethod
    def from_flex_analysis(
        cls, file: str | Path, quantity_on: Literal["intensity", "area"] = "intensity"
    ) -> list[MassList]:
        """Create MassLists from a FlexAnalysis mass list file.

        The mass lists exported from FlexAnalysis is an Excel file.
        Each sheet in the file contains a mass list of a spectrum.
        This method returns a list of MassLists,
        each corresponding to a sheet in the file.

        Args:
            file: The path to the FlexAnalysis mass list file.
            quantity_on: Whether the quantity is on intensity or area.
                Defaults to "intensity".

        Returns:
            A list of MassLists, each corresponding to a sheet in the file.
        """
        quantity_col = 2 if quantity_on == "intensity" else 6
        xlsx = pd.ExcelFile(file)
        dfs = [xlsx.parse(sheet, skiprows=2) for sheet in xlsx.sheet_names]
        results: list[MassList] = []
        for name, df in zip(xlsx.sheet_names, dfs):
            mz_a = df["m/z"].values
            intensity_a = df.iloc[:, quantity_col].values
            area_a = df["Area"].values
            sn_a = df["SN"].values
            results.append(cls(name, mz_a, intensity_a, area_a, sn_a))
        return results

    def calibrate(self, masses: Iterable[float], tol_ppm: float) -> None:
        """Linear calibration for the m/z values based on given masses.

        Args:
            masses: The masses to calibrate on.
            tol_ppm: The tolerance in ppm for matching peaks.

        Raises:
            ValueError: If no peaks are matched.
        """
        masses = np.array(masses)
        raw_masses = np.empty_like(masses)
        for i, mass in enumerate(masses):
            # Find the peak with strongest intensity within the tolerance.
            tol = mass * tol_ppm / 1e6
            mask = np.abs(self._raw_mz_a - mass) <= tol
            if not np.any(mask):
                raw_masses[i] = np.nan
                continue
            raw_masses[i] = self._raw_mz_a[mask][np.argmax(self._intensity_a[mask])]

        # Remove NaNs.
        mask = ~np.isnan(raw_masses)
        if sum(mask) < 2:
            raise ValueError("Less than two peaks are matched for calibration.")
        masses = masses[mask]
        raw_masses = raw_masses[mask]

        # Linear regression.
        slope, intercept = np.polyfit(raw_masses, masses, deg=1)
        self._calibrated_mz_a = slope * self._raw_mz_a + intercept

    def __len__(self) -> int:
        return self._raw_mz_a.size

    def __iter__(self) -> Iterator[Peak]:
        try:
            calibrated_mz_a = self._calibrated_mz_a
        except AttributeError:
            calibrated_mz_a = [None] * len(self._raw_mz_a)
        for raw_mz, calibrated_mz, intensity, area, sn in zip(
            self._raw_mz_a,
            calibrated_mz_a,
            self._intensity_a,
            self._area_a,
            self._sn_a,
        ):
            yield Peak(raw_mz, calibrated_mz, intensity, area, sn)
