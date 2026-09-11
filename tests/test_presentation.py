import numpy as np
import pytest

from transit_lab.analysis import run_bls
from transit_lab.data import load_demo_dataset
from transit_lab.presentation import (
    build_candidate_evidence,
    format_depth_percent,
    format_duration_hours,
    format_signal_to_noise,
)


def test_candidate_evidence_formats_computed_metrics_with_units() -> None:
    dataset = load_demo_dataset()
    candidate = run_bls(dataset.light_curve).best_candidate

    evidence = build_candidate_evidence(
        candidate,
        reference_period_days=dataset.target.reference_period_days,
        rank=1,
    )

    assert evidence.period == "1.76299 days"
    assert evidence.reference_offset == "0.9 min from archive"
    assert evidence.depth == "0.422%"
    assert evidence.duration == "2.40 hours"
    assert evidence.depth_signal_to_noise == "174.4"
    assert "0.9 minutes" in evidence.interpretation


def test_candidate_evidence_identifies_integer_period_multiples() -> None:
    dataset = load_demo_dataset()
    candidate = run_bls(dataset.light_curve).candidates[1]

    evidence = build_candidate_evidence(
        candidate,
        reference_period_days=dataset.target.reference_period_days,
        rank=2,
    )

    assert evidence.reference_offset == "1.763 days from archive"
    assert "2×" in evidence.interpretation
    assert "integer multiple" in evidence.interpretation


@pytest.mark.parametrize("value", [None, np.nan, -1.0])
def test_depth_formatter_handles_missing_or_invalid_measurements(value: float | None) -> None:
    assert format_depth_percent(value) == "Not available"


@pytest.mark.parametrize("value", [None, np.nan, 0.0, -1.0])
def test_duration_formatter_handles_missing_or_invalid_measurements(
    value: float | None,
) -> None:
    assert format_duration_hours(value) == "Not available"


@pytest.mark.parametrize("value", [None, np.nan, -1.0])
def test_signal_to_noise_formatter_handles_missing_or_invalid_measurements(
    value: float | None,
) -> None:
    assert format_signal_to_noise(value) == "Not available"
