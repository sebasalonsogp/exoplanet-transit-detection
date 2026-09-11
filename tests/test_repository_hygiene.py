import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).parents[1]
NOTEBOOK_PATH = REPOSITORY_ROOT / "assets" / "astro.ipynb"
ABSOLUTE_LOCAL_PATH = re.compile(
    r"(?:\b[A-Za-z]:[\\/]|/(?:Users|home)/[^/\s]+/)",
    flags=re.IGNORECASE,
)


def _walk_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_strings(key)
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def _load_notebook() -> dict[str, Any]:
    return json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))


def test_notebook_contains_no_absolute_local_paths() -> None:
    notebook = _load_notebook()

    matches = [text for text in _walk_strings(notebook) if ABSOLUTE_LOCAL_PATH.search(text)]

    assert not matches, "notebook contains machine-specific absolute paths"


def test_notebook_contains_no_saved_execution_state() -> None:
    notebook = _load_notebook()
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]

    assert code_cells, "notebook should retain its source code"
    assert all(cell.get("execution_count") is None for cell in code_cells)
    assert all(cell.get("outputs", []) == [] for cell in code_cells)
