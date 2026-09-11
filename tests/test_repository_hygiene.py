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
LIKELY_CREDENTIAL = re.compile(
    r"(?:"
    r"ghp_[A-Za-z0-9]{30,}|"
    r"github_pat_[A-Za-z0-9_]{50,}|"
    r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r")"
)
PUBLIC_TEXT_SUFFIXES = frozenset(
    {".ipynb", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
)
IGNORED_DIRECTORIES = frozenset({".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv"})


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


def _public_text_files() -> Iterator[Path]:
    return (
        path
        for path in REPOSITORY_ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in PUBLIC_TEXT_SUFFIXES
        and not IGNORED_DIRECTORIES.intersection(path.relative_to(REPOSITORY_ROOT).parts)
    )


def test_notebook_contains_no_absolute_local_paths() -> None:
    notebook = _load_notebook()

    matches = [text for text in _walk_strings(notebook) if ABSOLUTE_LOCAL_PATH.search(text)]

    assert not matches, "notebook contains machine-specific absolute paths"


def test_repository_contains_no_machine_specific_paths() -> None:
    matches = [
        str(path.relative_to(REPOSITORY_ROOT))
        for path in _public_text_files()
        if ABSOLUTE_LOCAL_PATH.search(path.read_text(encoding="utf-8"))
    ]

    assert not matches, f"repository contains machine-specific paths: {matches}"


def test_repository_contains_no_likely_credentials() -> None:
    matches = [
        str(path.relative_to(REPOSITORY_ROOT))
        for path in _public_text_files()
        if LIKELY_CREDENTIAL.search(path.read_text(encoding="utf-8"))
    ]

    assert not matches, f"repository contains likely credentials: {matches}"


def test_notebook_contains_no_saved_execution_state() -> None:
    notebook = _load_notebook()
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]

    assert code_cells, "notebook should retain its source code"
    assert all(cell.get("execution_count") is None for cell in code_cells)
    assert all(cell.get("outputs", []) == [] for cell in code_cells)
