"""Deterministic transit-search analysis independent of the Streamlit UI."""

from dataclasses import dataclass

import numpy as np
from astropy.timeseries import BoxLeastSquares
from numpy.typing import NDArray

from transit_lab.models import LightCurve


@dataclass(frozen=True, slots=True)
class BLSConfig:
    """Explicit search bounds matching the source notebook's BLS workflow."""

    minimum_period_days: float = 1.0
    maximum_period_days: float = 10.0
    transit_duration_days: float = 0.1
    frequency_factor: float = 1.0
    candidate_count: int = 3
    candidate_separation_days: float = 0.05


@dataclass(frozen=True, slots=True)
class TransitCandidate:
    """Measurements for one locally optimal BLS period."""

    period_days: float
    power: float
    transit_time_btjd: float
    duration_days: float
    depth_fraction: float
    depth_signal_to_noise: float


@dataclass(frozen=True, slots=True)
class BLSResult:
    """Periodogram, ranked candidates, and samples folded on the best period."""

    period_days: NDArray[np.float64]
    power: NDArray[np.float64]
    candidates: tuple[TransitCandidate, ...]
    folded_phase: NDArray[np.float64]
    folded_flux: NDArray[np.float64]

    @property
    def best_candidate(self) -> TransitCandidate:
        """Return the strongest candidate in the ranked result."""

        return self.candidates[0]


def _validate_config(config: BLSConfig) -> None:
    valid = (
        0 < config.minimum_period_days < config.maximum_period_days
        and 0 < config.transit_duration_days < config.minimum_period_days
        and config.frequency_factor > 0
        and config.candidate_count > 0
        and config.candidate_separation_days > 0
    )
    if not valid:
        raise ValueError("BLS configuration has invalid search bounds or candidate settings")


def _rank_candidate_indices(
    period_days: NDArray[np.float64],
    power: NDArray[np.float64],
    config: BLSConfig,
) -> list[int]:
    local_maxima = np.flatnonzero(
        (power[1:-1] > power[:-2]) & (power[1:-1] >= power[2:])
    ) + 1
    ranked = local_maxima[np.argsort(power[local_maxima])[::-1]]

    selected: list[int] = []
    for index in ranked:
        candidate_period = period_days[index]
        if all(
            abs(candidate_period - period_days[earlier]) >= config.candidate_separation_days
            for earlier in selected
        ):
            selected.append(int(index))
        if len(selected) == config.candidate_count:
            break

    if len(selected) < config.candidate_count:
        raise ValueError("BLS search returned too few distinct candidate periods")
    return selected


def run_bls(curve: LightCurve, config: BLSConfig | None = None) -> BLSResult:
    """Run Box Least Squares and fold the curve on its strongest candidate."""

    search = config or BLSConfig()
    _validate_config(search)

    model = BoxLeastSquares(curve.time, curve.flux, dy=curve.flux_error)
    periodogram = model.autopower(
        search.transit_duration_days,
        objective="likelihood",
        method="fast",
        oversample=10,
        minimum_n_transit=3,
        minimum_period=search.minimum_period_days,
        maximum_period=search.maximum_period_days,
        frequency_factor=search.frequency_factor,
    )
    period_days = np.asarray(periodogram.period, dtype=np.float64)
    power = np.asarray(periodogram.power, dtype=np.float64)
    indices = _rank_candidate_indices(period_days, power, search)

    candidates = tuple(
        TransitCandidate(
            period_days=float(period_days[index]),
            power=float(power[index]),
            transit_time_btjd=float(periodogram.transit_time[index]),
            duration_days=float(periodogram.duration[index]),
            depth_fraction=float(periodogram.depth[index]),
            depth_signal_to_noise=float(periodogram.depth_snr[index]),
        )
        for index in indices
    )

    best = candidates[0]
    phase = (
        (curve.time - best.transit_time_btjd + 0.5 * best.period_days) % best.period_days
    ) / best.period_days - 0.5
    order = np.argsort(phase)

    return BLSResult(
        period_days=period_days,
        power=power,
        candidates=candidates,
        folded_phase=np.asarray(phase[order], dtype=np.float64),
        folded_flux=np.asarray(curve.flux[order], dtype=np.float64),
    )
