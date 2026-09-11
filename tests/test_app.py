import json
from pathlib import Path
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from transit_lab.analysis import run_bls
from transit_lab.data import DataValidationError

APP_PATH = Path(__file__).parents[1] / "app.py"


def test_app_renders_project_identity_without_errors() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "Transit Lab"
    assert "Observe" in app.markdown[1].value


def test_app_tells_the_full_detection_story_by_default() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    headers = [header.value for header in app.header]
    metrics = {metric.label: metric.value for metric in app.metric}
    assert not app.exception
    assert headers == [
        "1. Observe the stellar signal",
        "2. Prepare the signal",
        "3. Compare detection methods",
        "4. Search for repeating dips",
        "5. Fold a candidate",
        "6. Interpret the evidence",
    ]
    assert metrics["Target"] == "KOI-13 b"
    assert metrics["Observations"] == "18,420"
    assert metrics["Best BLS period"].endswith("days")
    assert len(app.get("plotly_chart")) == 5
    assert app.segmented_control(key="preparation-mode").value == "Normalized"
    assert app.segmented_control(key="comparison-method").value == "Box Least Squares"
    assert app.segmented_control(key="candidate-period").value == "#1 · 1.76299 d"


def test_app_explains_each_signal_preparation_mode() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    selector = app.segmented_control(key="preparation-mode")

    assert [option.content for option in selector.proto.options] == [
        "Raw",
        "Normalized",
        "Detrended",
    ]
    expected_explanations = {
        "Raw": "instrument units",
        "Normalized": "median brightness equals one",
        "Detrended": "slow baseline changes",
    }
    for mode, phrase in expected_explanations.items():
        app = selector.set_value(mode).run()
        selector = app.segmented_control(key="preparation-mode")
        assert not app.exception
        assert phrase in " ".join(element.value for element in app.markdown)


def test_app_compares_each_method_and_keeps_bls_recommended() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    selector = app.segmented_control(key="comparison-method")

    assert [option.content for option in selector.proto.options] == [
        "Fourier transform",
        "SVD-assisted Fourier",
        "Box Least Squares",
    ]
    expected_explanations = {
        "Fourier transform": "sinusoidal basis",
        "SVD-assisted Fourier": "rank-6 reconstruction",
        "Box Least Squares": "box-shaped model",
    }
    for method, phrase in expected_explanations.items():
        app = selector.set_value(method).run()
        selector = app.segmented_control(key="comparison-method")
        assert not app.exception
        assert phrase in " ".join(element.value for element in app.markdown)

    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Fourier candidate"].endswith("days")
    assert metrics["SVD + Fourier candidate"].endswith("days")
    assert metrics["BLS candidate"].endswith("days")
    assert "external catalog" in " ".join(element.value for element in app.markdown)


def test_app_keeps_candidate_fold_and_evidence_synchronized() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    selector = app.segmented_control(key="candidate-period")

    expected = {
        "#1 · 1.76299 d": ("1.76299 days", "0.9 min from archive", "0.9 minutes"),
        "#2 · 3.52671 d": ("3.52671 days", "1.763 days from archive", "2×"),
        "#3 · 5.29244 d": ("5.29244 days", "3.529 days from archive", "3×"),
    }
    assert [option.content for option in selector.proto.options] == list(expected)

    folded_phases: set[str] = set()
    for label, (period, offset, relationship) in expected.items():
        app = selector.set_value(label).run()
        selector = app.segmented_control(key="candidate-period")
        metrics = {metric.label: metric for metric in app.metric}
        folded_spec = json.loads(app.get("plotly_chart")[-1].proto.spec)

        assert not app.exception
        assert metrics["Selected period"].value == period
        assert metrics["Selected period"].delta == offset
        assert relationship in app.info[0].value
        folded_phases.add(folded_spec["data"][0]["x"]["bdata"])

    assert len(folded_phases) == 3


def test_preparation_selection_updates_the_folded_signal_view() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    default_spec = json.loads(app.get("plotly_chart")[-1].proto.spec)
    assert default_spec["data"][0]["name"] == "Folded normalized observations"
    assert default_spec["layout"]["yaxis"]["title"]["text"] == "Normalized flux"

    app = app.segmented_control(key="preparation-mode").set_value("Raw").run()
    raw_spec = json.loads(app.get("plotly_chart")[-1].proto.spec)

    assert not app.exception
    assert raw_spec["data"][0]["name"] == "Folded raw observations"
    assert raw_spec["layout"]["yaxis"]["title"]["text"] == (
        "SAP flux (electrons/second)"
    )


def test_candidate_interactions_reuse_the_bounded_analysis_cache() -> None:
    st.cache_data.clear()
    with patch("transit_lab.run_bls", wraps=run_bls) as mocked_run_bls:
        app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
        app = (
            app.segmented_control(key="candidate-period")
            .set_value("#2 · 3.52671 d")
            .run()
        )
        app = app.segmented_control(key="preparation-mode").set_value("Raw").run()

    assert not app.exception
    assert mocked_run_bls.call_count == 1


def test_app_explains_evidence_sources_and_limitations() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    metrics = {metric.label: metric.value for metric in app.metric}

    assert metrics["Approximate depth"].endswith("%")
    assert metrics["Model duration"].endswith("hours")
    assert metrics["Depth signal-to-noise"]
    assert app.warning
    assert "does not confirm a planet" in app.warning[0].value
    assert "NASA Exoplanet Archive" in " ".join(
        element.value for element in app.markdown
    )


def test_app_turns_data_failures_into_a_useful_error() -> None:
    st.cache_data.clear()
    with patch(
        "transit_lab.load_demo_dataset",
        side_effect=DataValidationError("demo failure"),
    ):
        app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert app.error
    assert "could not load the bundled analysis" in app.error[0].value.lower()
