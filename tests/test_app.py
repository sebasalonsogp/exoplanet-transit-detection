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
        "2. Search for repeating dips",
        "3. Fold the strongest candidate",
    ]
    assert metrics["Target"] == "KOI-13 b"
    assert metrics["Observations"] == "18,420"
    assert metrics["Best BLS period"].endswith("days")
    assert len(app.get("plotly_chart")) == 3


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
