# Exoplanet Transit Lab

An interactive Streamlit workbench that turns a class notebook into a focused,
reproducible case study in scientific data engineering and visualization. Visitors can
follow one verified TESS light curve from raw observations through signal preparation,
method comparison, period search, phase folding, and evidence interpretation.

![Transit Lab dashboard showing the KOI-13 b summary and TESS light curve](docs/assets/dashboard-preview.png)

## Project origin

Transit Lab builds on a mini-project completed for **MTH 520**. The original class work
explored several signal-processing approaches for identifying periodic transit-shaped dips
in stellar light curves. This portfolio version preserves that analytical foundation while
expanding it into a reproducible application with typed data contracts, bounded interaction,
purpose-built visualizations, automated tests, continuous integration, and documented
scientific limitations. It is an engineering-focused repackaging of the course project, not
a claim of new astronomical research.

## Result

Transit Lab recovers a strongest Box Least Squares (BLS) period of **1.76299 days** for
KOI-13 b, approximately **0.9 minutes** from the 1.7635881-day NASA Exoplanet Archive
reference. The bundled observation contains **18,420** two-minute-cadence measurements
from TESS Sector 14.

The dashboard is deliberately interactive but bounded:

- Compare raw, median-normalized, and Savitzky–Golay-detrended views of the same signal.
- Contrast the notebook's Fourier and SVD-assisted Fourier approaches with BLS.
- Fold any of the three strongest BLS peaks without rerunning the expensive search.
- Inspect period, approximate depth, fixed model duration, signal-to-noise, provenance,
  and scientific limitations together.

The default view tells a complete story. Interaction reveals sensitivity to preparation
and period choice rather than unlocking required results.

## Engineering decisions

- **Offline and reproducible:** the analysis-ready TESS observation and deterministic
  comparison artifacts are versioned with the repository. The app makes no runtime data
  request.
- **One bounded cache entry:** loading, preparation, and BLS run once per server process;
  widget changes repeat only inexpensive folding and display formatting.
- **Typed analytical contracts:** immutable dataclasses validate aligned, finite light
  curves, candidate measurements, folded signals, and comparison results.
- **Purpose-built visualization:** Plotly charts preserve hover inspection while disabling
  zoom and drag interactions that could leave a reviewer in a confusing state.
- **Scope discipline:** the project reuses the notebook's signal-processing work. It does
  not add machine learning, live catalog search, user uploads, or new planetary validation.

See [the architecture notes](docs/architecture.md) for module boundaries and the execution
flow.

## Data and scientific provenance

The demonstration target is TIC 158324245 / TOI-1161.01, the KOI-13 system. The light curve
was exported from the SPOC TESS Sector 14 target-pixel product using Lightkurve's default
quality mask and pipeline aperture. Flux and uncertainty were divided by the median to
produce the normalized columns used by BLS.

Primary references:

- [MAST source Target Pixel File](https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:TESS/product/tess2019198215352-s0014-0000000158324245-0150-s_tp.fits)
- [MAST TESS data products](https://archive.stsci.edu/missions-and-data/tess/data-products)
- [NASA Exoplanet Archive KOI-13 overview](https://exoplanetarchive.ipac.caltech.edu/overview/KOI-13)
- [NASA Exoplanet Archive TAP documentation](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)
- [MAST data-use policy](https://archive.stsci.edu/publishing/data-use)

Detailed identifiers, processing steps, checksums, field definitions, and reference values
are recorded in [the data documentation](data/README.md) and
[`data/demo/target.json`](data/demo/target.json).

## Scientific limitations

BLS identifies a strong, repeating transit-shaped signal; it does not independently confirm
a planet or rule out eclipsing binaries, blended sources, stellar variability, or instrument
systematics. The archive provides the external confirmation. Dashboard depth is an
approximate BLS box-model measurement, and the displayed 2.40-hour duration is the fixed
0.1-day search duration rather than an independently fitted parameter. Higher-ranked periods
near two and three times the archive period are integer multiples of the same rhythm, not
separate detections.

## Run locally

Requirements: [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.12.

```powershell
git clone https://github.com/sebasalonsogp/exoplanet-transit-lab.git
cd exoplanet-transit-lab
uv sync --locked
uv run streamlit run app.py
```

Open `http://localhost:8501` if Streamlit does not open it automatically.

## Quality checks

```powershell
uv run pytest
uv run ruff check .
uv run mypy src app.py
```

The test suite covers data validation, preprocessing, BLS candidate ranking, phase folding,
comparison artifacts, presentation formatting, chart interaction constraints, and Streamlit
widget behavior. GitHub Actions runs the same checks for pull requests and pushes to `main`.

## Project structure

```text
app.py                      Streamlit narrative and interaction layer
src/transit_lab/            Typed data, analysis, comparison, and chart modules
data/demo/                  Versioned light curve, metadata, and method results
tests/                      Unit and Streamlit AppTest coverage
scripts/                    Deterministic artifact-generation utility
assets/astro.ipynb          Cleaned source class notebook
docs/architecture.md        Architecture and tradeoff notes
```

## Acknowledgements

This project uses public TESS observations produced by NASA's TESS mission and distributed
through MAST at the Space Telescope Science Institute. The project also references the NASA
Exoplanet Archive and the TESS Science Processing Operations Center pipeline.
