from pathlib import Path
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from transit_lab.data import DataValidationError

APP_PATH = Path(__file__).parents[1] / "app.py"


def test_app_renders_project_identity_without_errors() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "Transit Lab"
    assert "Observe" in app.markdown[1].value


def test_app_tells_the_observe_search_fold_story_by_default() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    headers = [header.value for header in app.header]
    metrics = {metric.label: metric.value for metric in app.metric}
    assert not app.exception
    assert headers == [
        "1. Observe the stellar signal",
        "2. Prepare the signal",
        "3. Compare detection methods",
        "4. Search for repeating dips",
        "5. Fold the strongest candidate",
    ]
    assert metrics["Target"] == "KOI-13 b"
    assert metrics["Observations"] == "18,420"
    assert metrics["Best BLS period"].endswith("days")
    assert len(app.get("plotly_chart")) == 5
    assert app.segmented_control(key="preparation-mode").value == "Detrended"
    assert app.segmented_control(key="comparison-method").value == "Box Least Squares"


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
