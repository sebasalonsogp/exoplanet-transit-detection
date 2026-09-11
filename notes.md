# Exoplanet Detector

## Project purpose

Build a polished, interactive portfolio project from the existing class notebook. The project is primarily for technical recruiters and data-science hiring managers, demonstrating strong analytical engineering, numerical reasoning, visualization, and dashboard design through a genuine interest in astronomy.

This is a presentation and software-engineering evolution of the original analysis, not a new astronomy research project.

## Product vision

Create a recruiter-friendly transit-analysis workbench that answers one question:

> Can we recover a known planetary transit from a noisy TESS light curve, and why does the selected analysis method matter?

The experience should make technical depth visible quickly, work as a guided story without interaction, and reward visitors who explore the controls. Its main differentiator is the comparison between methods that produce misleading periods and Box Least Squares, which is designed for box-shaped transit signals.

## Core experience

The dashboard follows one clear analytical narrative:

1. **Observe** — introduce a documented TESS target and visualize the raw stellar light curve.
2. **Prepare** — compare raw, normalized, and detrended flux.
3. **Compare** — show the existing Fourier, SVD-assisted, and Box Least Squares results.
4. **Search** — inspect the BLS periodogram and select from a small set of candidate periods.
5. **Fold** — phase-fold the observations at the selected period and reveal the transit shape.
6. **Interpret** — report the candidate period, depth, duration, signal score, and validation caveats.

The phase-folded transit is the main visual payoff. Interaction should demonstrate that preprocessing and period selection affect the conclusion, rather than provide decorative controls.

## Dashboard concept

Use a single-page analytical workbench with:

- A short project introduction and target context.
- A visible workflow: Observe → Prepare → Compare → Search → Fold → Interpret.
- One primary interactive chart at a time, supported by concise controls and explanations.
- Linked Plotly visualizations for the light curve, periodogram, and phase-folded transit.
- A method comparison for Fourier, SVD-assisted, and BLS using results already developed in the notebook.
- A compact evidence panel with key measurements and uncertainty-aware language.
- An optional “Under the hood” section explaining the mathematics, implementation, and limitations.

The default state must already tell a complete story. A visitor should not need to configure the analysis before seeing a strong result.

## MVP scope

- One verified, locally bundled TESS light curve.
- Reusable Python functions extracted from the exploratory notebook.
- Raw, normalized, and detrended signal views.
- Existing Fourier, SVD-assisted, and BLS comparison results.
- Interactive BLS periodogram with a few meaningful candidate periods.
- Linked phase-folded and binned transit visualization.
- Period, depth, approximate duration, signal score, and clear scientific caveats.
- Responsive, portfolio-quality dashboard styling and concise technical documentation.

## Data and computation strategy

- Bundle a cleaned and documented dataset so the public demo does not depend on a live NASA/MAST request.
- Keep the core BLS analysis reproducible from the bundled data.
- Cache or precompute expensive exploratory comparisons where live recomputation adds little visitor value.
- Limit controls to bounded, scientifically meaningful choices.
- Verify the target identity and reference values before presenting them as ground truth.

## Technical direction

- **Application:** Streamlit
- **Analysis:** NumPy, SciPy, Astropy, and Lightkurve where useful
- **Visualization:** Plotly
- **Testing:** pytest for data contracts and numerical pipeline behavior
- **Deployment:** a simple hosted Streamlit application using bundled, versioned data

The analysis layer should remain independent of Streamlit so it can be tested without rendering the dashboard.

## Design direction

Present the project as a modern scientific instrument rather than a generic corporate dashboard or an exaggerated mission-control interface:

- Dark navy or near-black analytical canvas.
- Restrained astronomical imagery and visual effects.
- Cyan for observations and amber for candidate signals.
- Large, editorial chart compositions instead of dense grids of KPI cards.
- Smooth visual continuity as the signal moves from raw observations to folded transit evidence.
- Progressive disclosure for mathematical and implementation detail.

## Explicit non-goals

- Live catalog search or repeated remote data downloads.
- Arbitrary file uploads in the initial version.
- Multi-star candidate browsing.
- Machine-learning detection.
- New denoising or exoplanet-validation research.
- Authentication, databases, or a separate web API.
- Automated claims that a detected signal confirms a planet.
- Heavy 3D visualization or decorative controls without analytical meaning.

## Success criteria

- A recruiter can understand the project’s purpose and technical result within two minutes.
- The dashboard demonstrates a clean end-to-end data pipeline rather than a collection of notebook cells.
- Interaction makes analytical consequences visible.
- The app runs reliably without external services.
- The codebase is small, modular, tested, and easy to explain in an interview.

## First implementation milestone

Reproduce the notebook’s BLS result from a verified local dataset through a small, tested analysis function, then render the raw light curve, periodogram, and phase-folded transit in a minimal Streamlit page.
