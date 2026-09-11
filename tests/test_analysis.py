import numpy as np
import pytest

from transit_lab.analysis import BLSConfig, run_bls
from transit_lab.data import load_demo_dataset


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
