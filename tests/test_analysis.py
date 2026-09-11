from dataclasses import replace

import numpy as np
import pytest

from transit_lab.analysis import (
    BLSConfig,
    DetrendConfig,
    detrend_light_curve,
    fold_light_curve,
    normalize_light_curve,
    prepare_signals,
    run_bls,
)
from transit_lab.data import load_demo_dataset
from transit_lab.models import LightCurve


def test_prepare_signals_preserves_samples_and_reproduces_bundled_normalization() -> None:
    dataset = load_demo_dataset()

    prepared = prepare_signals(dataset.raw_light_curve)

    assert prepared.raw is dataset.raw_light_curve
    assert np.array_equal(prepared.normalized.time, prepared.raw.time)
    assert np.array_equal(prepared.detrended.time, prepared.raw.time)
    assert prepared.normalized.observation_count == prepared.raw.observation_count
    assert prepared.detrended.observation_count == prepared.raw.observation_count
    assert np.median(prepared.normalized.flux) == pytest.approx(1.0)
    assert np.allclose(prepared.normalized.flux, dataset.light_curve.flux)
    assert np.median(prepared.detrended.flux) == pytest.approx(1.0, abs=1e-3)
    assert np.all(np.isfinite(prepared.detrended.flux))


def test_normalization_scales_flux_uncertainty() -> None:
    curve = LightCurve(
        time=np.arange(5, dtype=np.float64),
        flux=np.array([8.0, 9.0, 10.0, 11.0, 12.0]),
        flux_error=np.full(5, 0.5),
    )

    normalized = normalize_light_curve(curve)

    assert normalized.flux.tolist() == pytest.approx([0.8, 0.9, 1.0, 1.1, 1.2])
    assert normalized.flux_error is not None
    assert normalized.flux_error.tolist() == pytest.approx([0.05] * 5)


def test_normalization_rejects_nonpositive_median_flux() -> None:
    curve = LightCurve(
        time=np.arange(3, dtype=np.float64),
        flux=np.array([-1.0, 0.0, 1.0]),
    )

    with pytest.raises(ValueError, match="median flux must be positive"):
        normalize_light_curve(curve)


@pytest.mark.parametrize(
    "config",
    [
        DetrendConfig(window_length=4, polynomial_order=2),
        DetrendConfig(window_length=5, polynomial_order=5),
    ],
)
def test_detrending_rejects_invalid_filter_configuration(config: DetrendConfig) -> None:
    curve = LightCurve(
        time=np.arange(5, dtype=np.float64),
        flux=np.linspace(0.99, 1.01, 5),
    )

    with pytest.raises(ValueError, match="detrending configuration"):
        detrend_light_curve(curve, config)


def test_detrending_rejects_a_curve_shorter_than_the_filter_window() -> None:
    curve = LightCurve(
        time=np.arange(5, dtype=np.float64),
        flux=np.linspace(0.99, 1.01, 5),
    )

    with pytest.raises(ValueError, match="at least 7 samples"):
        detrend_light_curve(curve, DetrendConfig(window_length=7, polynomial_order=2))


def test_bls_recovers_the_verified_demo_period() -> None:
    dataset = load_demo_dataset()

    result = run_bls(dataset.light_curve)

    assert result.best_candidate.period_days == pytest.approx(
        dataset.target.reference_period_days,
        abs=0.01,
    )
    assert result.best_candidate.depth_fraction > 0
    assert result.best_candidate.duration_days == pytest.approx(0.1)
    assert result.best_candidate.depth_signal_to_noise > 0


def test_bls_returns_aligned_periodogram_and_folded_samples() -> None:
    dataset = load_demo_dataset()

    result = run_bls(dataset.light_curve)

    assert result.period_days.size == result.power.size
    assert result.period_days.size > 1_000
    assert result.period_days.min() >= BLSConfig().minimum_period_days
    assert result.period_days.max() <= BLSConfig().maximum_period_days
    assert result.folded_phase.size == dataset.light_curve.observation_count
    assert result.folded_flux.size == dataset.light_curve.observation_count
    assert np.all(np.isfinite(result.power))
    assert np.all((-0.5 <= result.folded_phase) & (result.folded_phase < 0.5))
    assert np.all(np.diff(result.folded_phase) >= 0)


def test_bls_returns_ranked_distinct_candidates() -> None:
    dataset = load_demo_dataset()
    config = BLSConfig(candidate_count=3, candidate_separation_days=0.05)

    result = run_bls(dataset.light_curve, config)

    powers = [candidate.power for candidate in result.candidates]
    periods = [candidate.period_days for candidate in result.candidates]
    assert len(result.candidates) == 3
    assert powers == sorted(powers, reverse=True)
    assert all(
        abs(period - earlier) >= config.candidate_separation_days
        for index, period in enumerate(periods)
        for earlier in periods[:index]
    )


def test_every_ranked_candidate_can_fold_the_same_curve() -> None:
    dataset = load_demo_dataset()
    result = run_bls(dataset.light_curve)

    folded_candidates = [
        fold_light_curve(dataset.light_curve, candidate)
        for candidate in result.candidates
    ]

    for folded in folded_candidates:
        assert folded.phase.size == dataset.light_curve.observation_count
        assert folded.flux.size == dataset.light_curve.observation_count
        assert np.all((-0.5 <= folded.phase) & (folded.phase < 0.5))
        assert np.all(np.diff(folded.phase) >= 0)
    assert not np.array_equal(folded_candidates[0].phase, folded_candidates[1].phase)


def test_folding_rejects_a_nonpositive_candidate_period() -> None:
    dataset = load_demo_dataset()
    candidate = replace(run_bls(dataset.light_curve).best_candidate, period_days=0.0)

    with pytest.raises(ValueError, match="candidate period"):
        fold_light_curve(dataset.light_curve, candidate)


@pytest.mark.parametrize(
    "config",
    [
        BLSConfig(minimum_period_days=2.0, maximum_period_days=2.0),
        BLSConfig(minimum_period_days=0.05, transit_duration_days=0.1),
        BLSConfig(candidate_count=0),
    ],
)
def test_bls_rejects_invalid_configuration(config: BLSConfig) -> None:
    dataset = load_demo_dataset()

    with pytest.raises(ValueError, match="BLS configuration"):
        run_bls(dataset.light_curve, config)
