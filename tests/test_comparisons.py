import json
from pathlib import Path

import numpy as np
import pytest

from transit_lab import load_demo_dataset, prepare_signals, run_bls
from transit_lab.comparisons import (
    ComparisonConfig,
    build_bls_comparison,
    generate_notebook_comparisons,
    load_packaged_comparisons,
)


def test_notebook_comparisons_share_one_period_score_contract() -> None:
    prepared = prepare_signals(load_demo_dataset().raw_light_curve)

    results = generate_notebook_comparisons(prepared.detrended)

    assert set(results) == {"fourier", "svd_fourier"}
    assert results["fourier"].candidate_period_days == pytest.approx(1.5989571)
    assert results["svd_fourier"].candidate_period_days == pytest.approx(1.0233326)
    for result in results.values():
        assert result.period_days.shape == result.score.shape
        assert result.period_days.size > 10
        assert np.all(np.diff(result.period_days) > 0)
        assert np.all(np.isfinite(result.score))
        assert np.min(result.score) >= 0
        assert np.max(result.score) == pytest.approx(1.0)
        assert result.period_days.min() >= ComparisonConfig().minimum_period_days
        assert result.period_days.max() <= ComparisonConfig().maximum_period_days


def test_packaged_comparisons_match_a_fresh_recomputation() -> None:
    prepared = prepare_signals(load_demo_dataset().raw_light_curve)
    packaged = load_packaged_comparisons()
    recomputed = generate_notebook_comparisons(prepared.detrended)

    assert packaged.keys() == recomputed.keys()
    for method_key in packaged:
        assert packaged[method_key].candidate_period_days == pytest.approx(
            recomputed[method_key].candidate_period_days
        )
        assert np.allclose(packaged[method_key].period_days, recomputed[method_key].period_days)
        assert np.allclose(packaged[method_key].score, recomputed[method_key].score)


def test_bls_result_uses_the_same_normalized_comparison_contract() -> None:
    dataset = load_demo_dataset()

    comparison = build_bls_comparison(run_bls(dataset.light_curve))

    assert comparison.key == "bls"
    assert comparison.recommended is True
    assert comparison.score.shape == comparison.period_days.shape
    assert np.max(comparison.score) == pytest.approx(1.0)
    assert comparison.candidate_period_days == pytest.approx(
        dataset.target.reference_period_days,
        abs=0.01,
    )


def test_packaged_comparison_loader_rejects_missing_methods(tmp_path: Path) -> None:
    artifact = tmp_path / "method_results.json"
    artifact.write_text(
        json.dumps({"schema_version": "1.0", "methods": {}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="required methods"):
        load_packaged_comparisons(artifact)
