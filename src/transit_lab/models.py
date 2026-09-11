"""Typed data contracts shared by the analysis and presentation layers."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class LightCurve:
    """Time-aligned stellar flux observations."""

    time: NDArray[np.float64]
    flux: NDArray[np.float64]
    flux_error: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        if self.time.ndim != 1 or self.flux.ndim != 1:
            raise ValueError("time and flux must be one-dimensional")
        if self.time.size != self.flux.size:
            raise ValueError("time and flux must contain the same number of samples")
        if self.time.size == 0:
            raise ValueError("light curve must contain at least one sample")
        if not np.all(np.isfinite(self.time)) or not np.all(np.isfinite(self.flux)):
            raise ValueError("time and flux must contain only finite values")
        if np.any(np.diff(self.time) <= 0):
            raise ValueError("time samples must be strictly increasing")
        if self.flux_error is not None:
            if self.flux_error.ndim != 1 or self.flux_error.size != self.time.size:
                raise ValueError("flux uncertainty must align with time and flux")
            if not np.all(np.isfinite(self.flux_error)):
                raise ValueError("flux uncertainty must contain only finite values")

    @property
    def observation_count(self) -> int:
        """Return the number of aligned observations."""

        return int(self.time.size)


@dataclass(frozen=True, slots=True)
class TargetMetadata:
    """Target identity and reference values needed by the application."""

    tic_id: int
    toi: str
    planet_name: str
    mission: str
    sector: int
    cadence_seconds: int
    reference_period_days: float
    aliases: tuple[str, ...] = ()
    camera: int | None = None
    ccd: int | None = None
    reference_transit_depth_ppm: float | None = None
    reference_transit_duration_hours: float | None = None
    source_product: str | None = None


@dataclass(frozen=True, slots=True)
class TransitDataset:
    """A validated light curve paired with its target metadata."""

    light_curve: LightCurve
    target: TargetMetadata
