"""Typed data contracts shared by the analysis and presentation layers."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class LightCurve:
    """Time-aligned stellar flux observations."""

    time: NDArray[np.float64]
    flux: NDArray[np.float64]

    def __post_init__(self) -> None:
        if self.time.size != self.flux.size:
            raise ValueError("time and flux must contain the same number of samples")

    @property
    def observation_count(self) -> int:
        """Return the number of aligned observations."""

        return int(self.time.size)
