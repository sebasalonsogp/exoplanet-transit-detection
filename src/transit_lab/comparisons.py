"""Notebook-derived method comparisons with a shared display contract."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from transit_lab.analysis import BLSResult
from transit_lab.models import LightCurve

DEFAULT_COMPARISON_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "demo" / "method_results.json"
)
REQUIRED_PACKAGED_METHODS = {"fourier", "svd_fourier"}


@dataclass(frozen=True, slots=True)
class ComparisonConfig:
    """Explicit bounds and SVD parameters adapted from the source notebook."""

    minimum_period_days: float = 1.0
    maximum_period_days: float = 10.0
    svd_window_size: int = 50
    svd_rank: int = 6


@dataclass(frozen=True, slots=True)
class MethodComparison:
    """One method's normalized period score and strongest candidate."""

    key: str
    label: str
    candidate_period_days: float
    period_days: NDArray[np.float64]
    score: NDArray[np.float64]
    interpretation: str
    parameter_summary: str
    recommended: bool = False

    def __post_init__(self) -> None:
        valid_series = (
            self.period_days.ndim == 1
            and self.score.ndim == 1
            and self.period_days.size == self.score.size
            and self.period_days.size > 0
            and np.all(np.isfinite(self.period_days))
            and np.all(np.isfinite(self.score))
            and np.all(np.diff(self.period_days) > 0)
            and np.all(self.score >= 0)
            and np.all(self.score <= 1)
        )
        if not valid_series or not np.isfinite(self.candidate_period_days):
            raise ValueError("method comparison contains an invalid period-score series")


def _validate_config(curve: LightCurve, config: ComparisonConfig) -> None:
    valid = (
        0 < config.minimum_period_days < config.maximum_period_days
        and 1 < config.svd_window_size <= curve.observation_count
        and 0 < config.svd_rank <= config.svd_window_size
    )
    if not valid:
        raise ValueError("comparison configuration has invalid period or SVD settings")


def _period_score(
    signal: NDArray[np.float64],
    time: NDArray[np.float64],
    config: ComparisonConfig,
) -> tuple[NDArray[np.float64], NDArray[np.float64], float]:
    sample_interval = float(np.median(np.diff(time)))
    frequencies = np.fft.rfftfreq(signal.size, d=sample_interval)[1:]
    power = np.abs(np.fft.rfft(signal - np.mean(signal))[1:]) ** 2
    periods = 1.0 / frequencies
    in_range = (periods >= config.minimum_period_days) & (
        periods <= config.maximum_period_days
    )
    periods = periods[in_range]
    power = power[in_range]
    if periods.size == 0 or float(np.max(power)) <= 0:
        raise ValueError("comparison spectrum contains no positive in-range power")

    order = np.argsort(periods)
    period_days = np.asarray(periods[order], dtype=np.float64)
    score = np.asarray(power[order] / np.max(power), dtype=np.float64)
    candidate_period = float(period_days[int(np.argmax(score))])
    return period_days, score, candidate_period


def _svd_residual(curve: LightCurve, config: ComparisonConfig) -> NDArray[np.float64]:
    windows = np.lib.stride_tricks.sliding_window_view(
        curve.flux,
        window_shape=config.svd_window_size,
    )
    left_vectors, singular_values, right_vectors = np.linalg.svd(
        windows,
        full_matrices=False,
    )
    reconstructed_windows = (
        left_vectors[:, : config.svd_rank] * singular_values[: config.svd_rank]
    ) @ right_vectors[: config.svd_rank, :]

    reconstructed_sum = np.zeros(curve.observation_count, dtype=np.float64)
    contribution_count = np.zeros(curve.observation_count, dtype=np.float64)
    for offset in range(config.svd_window_size):
        stop = offset + reconstructed_windows.shape[0]
        reconstructed_sum[offset:stop] += reconstructed_windows[:, offset]
        contribution_count[offset:stop] += 1

    reconstructed = reconstructed_sum / contribution_count
    return np.asarray(curve.flux - reconstructed, dtype=np.float64)


def generate_notebook_comparisons(
    detrended_curve: LightCurve,
    config: ComparisonConfig | None = None,
) -> dict[str, MethodComparison]:
    """Regenerate the bounded Fourier and rank-6 SVD-assisted comparisons."""

    settings = config or ComparisonConfig()
    _validate_config(detrended_curve, settings)
    fourier_period, fourier_score, fourier_candidate = _period_score(
        detrended_curve.flux,
        detrended_curve.time,
        settings,
    )
    svd_period, svd_score, svd_candidate = _period_score(
        _svd_residual(detrended_curve, settings),
        detrended_curve.time,
        settings,
    )

    return {
        "fourier": MethodComparison(
            key="fourier",
            label="Fourier transform",
            candidate_period_days=fourier_candidate,
            period_days=fourier_period,
            score=fourier_score,
            interpretation=(
                "A sinusoidal basis spreads sharp transit edges across harmonics, biasing "
                "the strongest period in this light curve."
            ),
            parameter_summary="FFT of detrended normalized flux · 1–10 day period window",
        ),
        "svd_fourier": MethodComparison(
            key="svd_fourier",
            label="SVD-assisted Fourier",
            candidate_period_days=svd_candidate,
            period_days=svd_period,
            score=svd_score,
            interpretation=(
                "A rank-6 reconstruction removes dominant structure first, but its residual "
                "spectrum still favors a different period."
            ),
            parameter_summary=(
                f"{settings.svd_window_size}-sample windows · rank {settings.svd_rank} · "
                "FFT of reconstruction residual"
            ),
        ),
    }


def build_bls_comparison(result: BLSResult) -> MethodComparison:
    """Adapt a live BLS result to the normalized comparison contract."""

    maximum_power = float(np.max(result.power))
    if maximum_power <= 0:
        raise ValueError("BLS comparison requires positive power")
    return MethodComparison(
        key="bls",
        label="Box Least Squares",
        candidate_period_days=result.best_candidate.period_days,
        period_days=result.period_days,
        score=np.asarray(result.power / maximum_power, dtype=np.float64),
        interpretation=(
            "The box-shaped model matches short transit dips, concentrating the strongest "
            "score near the archive period."
        ),
        parameter_summary="0.1-day transit duration · 1–10 day period window",
        recommended=True,
    )


def comparison_artifact_payload(
    results: dict[str, MethodComparison],
    config: ComparisonConfig | None = None,
) -> dict[str, object]:
    """Convert generated comparisons into the versioned JSON artifact schema."""

    settings = config or ComparisonConfig()
    return {
        "schema_version": "1.0",
        "source_notebook": "assets/astro.ipynb",
        "source_dataset": "data/demo/light_curve.csv",
        "input_signal": "Savitzky-Golay-detrended normalized SAP flux",
        "parameters": {
            "minimum_period_days": settings.minimum_period_days,
            "maximum_period_days": settings.maximum_period_days,
            "svd_window_size": settings.svd_window_size,
            "svd_rank": settings.svd_rank,
            "fourier_transform": "numpy.fft.rfft",
        },
        "methods": {
            key: {
                "key": result.key,
                "label": result.label,
                "candidate_period_days": result.candidate_period_days,
                "period_days": result.period_days.tolist(),
                "score": result.score.tolist(),
                "interpretation": result.interpretation,
                "parameter_summary": result.parameter_summary,
            }
            for key, result in results.items()
        },
    }


def _comparison_from_payload(payload: dict[str, Any]) -> MethodComparison:
    return MethodComparison(
        key=str(payload["key"]),
        label=str(payload["label"]),
        candidate_period_days=float(payload["candidate_period_days"]),
        period_days=np.asarray(payload["period_days"], dtype=np.float64),
        score=np.asarray(payload["score"], dtype=np.float64),
        interpretation=str(payload["interpretation"]),
        parameter_summary=str(payload["parameter_summary"]),
    )


def load_packaged_comparisons(path: Path | None = None) -> dict[str, MethodComparison]:
    """Load and validate the precomputed notebook comparison artifact."""

    artifact_path = path or DEFAULT_COMPARISON_PATH
    try:
        payload: dict[str, Any] = json.loads(artifact_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "1.0":
            raise ValueError("unsupported method comparison schema")
        methods = payload["methods"]
        if not isinstance(methods, dict) or not REQUIRED_PACKAGED_METHODS.issubset(methods):
            raise ValueError("method comparison artifact is missing required methods")
        return {
            key: _comparison_from_payload(methods[key])
            for key in sorted(REQUIRED_PACKAGED_METHODS)
        }
    except OSError as error:
        raise ValueError(f"unable to read method comparison artifact: {error}") from error
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"invalid method comparison artifact: {error}") from error
