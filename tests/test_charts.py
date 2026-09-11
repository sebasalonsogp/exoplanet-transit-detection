import numpy as np

from transit_lab.analysis import run_bls
from transit_lab.charts import (
    build_folded_chart,
    build_light_curve_chart,
    build_periodogram_chart,
)
from transit_lab.data import load_demo_dataset


def test_light_curve_chart_contains_every_observation() -> None:
    dataset = load_demo_dataset()

    figure = build_light_curve_chart(dataset.light_curve)

    assert figure.data[0].name == "TESS observations"
    assert len(figure.data[0].x) == dataset.light_curve.observation_count
    assert figure.layout.xaxis.title.text == "Time (BTJD)"
    assert figure.layout.yaxis.title.text == "Normalized flux"


def test_periodogram_chart_marks_ranked_candidates_and_reference() -> None:
    dataset = load_demo_dataset()
    result = run_bls(dataset.light_curve)

    figure = build_periodogram_chart(result, dataset.target.reference_period_days)

    assert len(figure.data[0].x) == result.period_days.size
    assert len(figure.data[1].x) == len(result.candidates)
    assert len(figure.layout.shapes) == 1
    assert figure.layout.xaxis.title.text == "Trial period (days)"
    assert figure.layout.yaxis.title.text == "BLS log-likelihood power"


def test_folded_chart_layers_observations_and_binned_median() -> None:
    dataset = load_demo_dataset()
    result = run_bls(dataset.light_curve)

    figure = build_folded_chart(result)

    assert [trace.name for trace in figure.data] == ["Folded observations", "Binned median"]
    assert len(figure.data[0].x) == dataset.light_curve.observation_count
    assert len(figure.data[1].x) < len(figure.data[0].x)
    assert np.min(figure.data[0].x) >= -0.5
    assert np.max(figure.data[0].x) < 0.5
    assert figure.layout.xaxis.title.text == "Orbital phase"
