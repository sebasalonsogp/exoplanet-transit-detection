from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_renders_project_identity_without_errors() -> None:
    app_path = Path(__file__).parents[1] / "app.py"

    app = AppTest.from_file(str(app_path)).run()

    assert not app.exception
    assert app.title[0].value == "Transit Lab"
    assert "Observe" in app.markdown[1].value
