"""Deterministic transit-search analysis independent of the Streamlit UI."""

from dataclasses import dataclass

import numpy as np
from astropy.timeseries import BoxLeastSquares
from numpy.typing import NDArray
from scipy.signal import savgol_filter

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
class DetrendConfig:
    """Savitzky-Golay settings reused from the source notebook."""

    window_length: int = 101
    polynomial_order: int = 3


@dataclass(frozen=True, slots=True)
class PreparedSignals:
    """Aligned raw, normalized, and detrended views of one light curve."""

    raw: LightCurve
    normalized: LightCurve
    detrended: LightCurve


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
class FoldedSignal:
    """Flux samples ordered on a candidate's normalized orbital phase."""

    phase: NDArray[np.float64]
    flux: NDArray[np.float64]

    def __post_init__(self) -> None:
        valid = (
            self.phase.ndim == 1
            and self.flux.ndim == 1
            and self.phase.size == self.flux.size
            and self.phase.size > 0
            and np.all(np.isfinite(self.phase))
            and np.all(np.isfinite(self.flux))
            and np.all((-0.5 <= self.phase) & (self.phase < 0.5))
            and np.all(np.diff(self.phase) >= 0)
        )
        if not valid:
            raise ValueError("folded signal must contain aligned, finite, phase-ordered samples")


@dataclass(frozen=True, slots=True)
class BLSResult:
    """Periodogram, ranked candidates, and samples folded on the best period."""

    period_days: NDArray[np.float64]
    power: NDArray[np.float64]
    candidates: tuple[TransitCandidate, ...]
    folded_signal: FoldedSignal

    @property
    def best_candidate(self) -> TransitCandidate:
        """Return the strongest candidate in the ranked result."""

        return self.candidates[0]

    @property
    def folded_phase(self) -> NDArray[np.float64]:
        """Return the best candidate's folded phase for compatibility."""

        return self.folded_signal.phase

    @property
    def folded_flux(self) -> NDArray[np.float64]:
        """Return the best candidate's phase-ordered flux for compatibility."""

        return self.folded_signal.flux


def normalize_light_curve(curve: LightCurve) -> LightCurve:
    """Scale a flux series and its uncertainty by the median flux."""

    median_flux = float(np.median(curve.flux))
    if median_flux <= 0:
        raise ValueError("median flux must be positive for normalization")

    normalized_error = (
        None if curve.flux_error is None else curve.flux_error / median_flux
    )
    return LightCurve(
        time=curve.time,
        flux=np.asarray(curve.flux / median_flux, dtype=np.float64),
        flux_error=(
            None
            if normalized_error is None
            else np.asarray(normalized_error, dtype=np.float64)
        ),
    )


def _validate_detrend_config(curve: LightCurve, config: DetrendConfig) -> None:
    valid = (
        config.window_length > 0
        and config.window_length % 2 == 1
        and 0 <= config.polynomial_order < config.window_length
    )
    if not valid:
        raise ValueError(
            "detrending configuration requires an odd window above the polynomial order"
        )
    if curve.observation_count < config.window_length:
        raise ValueError(
            f"detrending requires at least {config.window_length} samples for this filter window"
        )


def detrend_light_curve(
    curve: LightCurve,
    config: DetrendConfig | None = None,
) -> LightCurve:
    """Divide normalized flux by the notebook's smooth Savitzky-Golay trend."""

    settings = config or DetrendConfig()
    _validate_detrend_config(curve, settings)
    trend = np.asarray(
        savgol_filter(
            curve.flux,
            window_length=settings.window_length,
            polyorder=settings.polynomial_order,
            mode="interp",
        ),
        dtype=np.float64,
    )
    zero_tolerance = np.finfo(np.float64).eps * max(1.0, float(np.max(np.abs(trend))))
    if np.any(np.abs(trend) <= zero_tolerance):
        raise ValueError("detrending trend contains values too close to zero")

    detrended_error = None if curve.flux_error is None else curve.flux_error / np.abs(trend)
    return LightCurve(
        time=curve.time,
        flux=np.asarray(curve.flux / trend, dtype=np.float64),
        flux_error=(
            None
            if detrended_error is None
            else np.asarray(detrended_error, dtype=np.float64)
        ),
    )


def prepare_signals(
    raw_curve: LightCurve,
    detrend_config: DetrendConfig | None = None,
) -> PreparedSignals:
    """Build the three notebook-derived signal preparation views."""

    normalized = normalize_light_curve(raw_curve)
    return PreparedSignals(
        raw=raw_curve,
        normalized=normalized,
        detrended=detrend_light_curve(normalized, detrend_config),
    )


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


def fold_light_curve(curve: LightCurve, candidate: TransitCandidate) -> FoldedSignal:
    """Fold one light curve on a validated transit-period candidate."""

    if not np.isfinite(candidate.period_days) or candidate.period_days <= 0:
        raise ValueError("candidate period must be a positive finite number")
    if not np.isfinite(candidate.transit_time_btjd):
        raise ValueError("candidate transit time must be finite")

    phase = (
        (curve.time - candidate.transit_time_btjd + 0.5 * candidate.period_days)
        % candidate.period_days
    ) / candidate.period_days - 0.5
    order = np.argsort(phase)
    return FoldedSignal(
        phase=np.asarray(phase[order], dtype=np.float64),
        flux=np.asarray(curve.flux[order], dtype=np.float64),
    )


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
    return BLSResult(
        period_days=period_days,
        power=power,
        candidates=candidates,
        folded_signal=fold_light_curve(curve, best),
    )
