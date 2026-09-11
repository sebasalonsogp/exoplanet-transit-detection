# Exoplanet Transit Lab

An interactive Streamlit workbench that repackages an exploratory class project into a
clear, recruiter-friendly investigation of exoplanet transit detection.

The initial scaffold establishes the application shell, typed analysis contracts, tests,
and project tooling. Scientific analysis will be added incrementally from the original
notebook.

## Development

```powershell
uv sync
uv run streamlit run app.py
```

Run the quality checks:

```powershell
uv run pytest
uv run ruff check .
uv run mypy
```

## Planned analytical flow

Observe → Prepare → Compare → Search → Fold → Interpret
