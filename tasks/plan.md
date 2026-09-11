# Implementation plan: Exoplanet Transit Lab

## Overview

Build a polished, single-page Streamlit workbench from the existing class notebook. The
project should demonstrate analytical engineering, numerical reasoning, testing, and data
visualization to technical recruiters and data-science hiring managers without becoming a
new astronomy research project.

The implementation is deliberately incremental. The first product milestone is a complete
vertical slice that loads one bundled TESS light curve, reproduces a Box Least Squares (BLS)
result, and renders the raw signal, periodogram, and folded transit. Later phases add the
notebook's preprocessing and comparison story, bounded interaction, interpretation, and
portfolio polish.

## Release boundary

The **portfolio MVP** is complete after Phase 3. Phase 4 makes it ready to publish and share.
Anything listed under “Deferred ideas” is outside the approved scope unless the plan is
revisited.

## Architecture decisions

- Keep one deployable Streamlit application with a thin root `app.py`; do not add an API,
  database, authentication, or multipage routing.
- Keep reusable numerical and data logic under `src/transit_lab/`, independent of Streamlit.
- Bundle one cleaned, documented dataset so the public app has no live NASA/MAST dependency.
- Recompute the BLS result from local data. Cache or precompute Fourier/SVD comparisons when
  live execution adds latency without improving the visitor experience.
- Use one charting stack for the analytical figures. Plotly remains the planned choice because
  the approved vision calls for precise hover detail and scientific chart composition.
- Keep interaction bounded and meaningful: signal preparation, method view, and a small set of
  candidate periods. Do not accept arbitrary uploads in the MVP.
- Use Streamlit-native layout, theme, status, and widget features first. Avoid custom CSS and
  custom components unless a specific design requirement cannot be met natively.
- Unit-test pure logic with pytest and use `st.testing.v1.AppTest` for page behavior. Candidate
  selection will use a normal widget rather than relying on chart-selection events that
  AppTest cannot simulate.

## Dependency graph

```text
Sanitized source notebook
        |
        v
Verified, documented local dataset
        |
        v
Data contracts and loader
        |
        +----------------------+
        |                      |
        v                      v
Reproducible BLS          Preparation and
analysis                  comparison results
        |                      |
        +----------+-----------+
                   v
          Interactive workbench
                   |
                   v
       Interpretation and caveats
                   |
                   v
       Polish, documentation, CI,
            deployment readiness
```

## Phase 0: Source hygiene and evidence

### Task 1: Sanitize the archived notebook

**Description:** Preserve the notebook as project provenance while removing machine-specific
execution artifacts. Clear cell outputs and execution counts, replace any required absolute
paths with repository-relative examples, and add a regression check so local paths cannot be
reintroduced accidentally.

**Acceptance criteria:**

- [ ] `assets/astro.ipynb` contains no Windows drive paths, user-home paths, or secrets.
- [ ] All code-cell outputs and execution counts are cleared without deleting source or Markdown.
- [ ] An automated repository-hygiene test detects absolute local paths in the notebook.

**Verification:**

- [ ] `uv run pytest tests/test_repository_hygiene.py`
- [ ] Open the notebook and confirm its narrative and code remain readable.

**Dependencies:** None

**Files likely touched:**

- `assets/astro.ipynb`
- `tests/test_repository_hygiene.py`

**Estimated scope:** Small (2 files)

### Task 2: Establish the verified demo data package

**Description:** Identify the exact target used by the notebook, verify its identity and
reference transit values against authoritative astronomy sources, and export only the cleaned
time/flux observations and metadata needed by the app. Document provenance, units, processing,
and redistribution terms.

**Acceptance criteria:**

- [ ] The bundled dataset has explicit time and normalized-flux columns with finite values.
- [ ] Target identity, sector/observation context, units, source URLs, and reference values are
  recorded in metadata and `data/README.md`.
- [ ] The application can use the local package without network access or an absolute path.

**Verification:**

- [ ] Inspect the metadata against the cited NASA Exoplanet Archive/MAST records.
- [ ] Run an offline load check from the repository root.

**Dependencies:** Task 1

**Files likely touched:**

- `data/demo/light_curve.csv`
- `data/demo/target.json`
- `data/README.md`

**Estimated scope:** Medium (3 files)

### Checkpoint A: Clean and trustworthy source

- [ ] Notebook hygiene test passes.
- [ ] Data provenance and reference values have been reviewed by the user.
- [ ] No runtime network request or local machine path is required.
- [ ] Human review before Phase 1.

## Phase 1: First end-to-end analytical slice

### Task 3: Implement the data contract and loader

**Description:** Extend the typed domain model and add a small loader for the bundled dataset.
Validate aligned samples, finite numeric values, ordering, required metadata, and friendly
failure messages before analysis begins.

**Acceptance criteria:**

- [ ] The loader returns typed light-curve and target-metadata objects.
- [ ] Invalid columns, non-finite values, misaligned samples, and empty data fail clearly.
- [ ] Loading uses repository-relative resources and contains no Streamlit calls.

**Verification:**

- [ ] `uv run pytest tests/test_data.py tests/test_models.py`
- [ ] `uv run mypy`

**Dependencies:** Task 2

**Files likely touched:**

- `src/transit_lab/models.py`
- `src/transit_lab/data.py`
- `tests/test_data.py`
- `tests/test_models.py`

**Estimated scope:** Medium (4 files)

### Task 4: Reproduce the BLS result

**Description:** Extract the notebook's BLS workflow into a deterministic analysis function
using the smallest suitable scientific dependency set. Return period-grid power, ranked
candidates, folded phase/flux, and summary measurements without UI concerns.

**Acceptance criteria:**

- [ ] The best candidate period matches the verified reference within a documented tolerance.
- [ ] The result includes periodogram values, folded samples, approximate depth/duration, and a
  clearly named signal-strength measure.
- [ ] Inputs, search bounds, units, and any numerical assumptions are explicit and tested.

**Verification:**

- [ ] `uv run pytest tests/test_analysis.py`
- [ ] `uv run ruff check . && uv run mypy`

**Dependencies:** Task 3

**Files likely touched:**

- `pyproject.toml`
- `uv.lock`
- `src/transit_lab/analysis.py`
- `tests/test_analysis.py`

**Estimated scope:** Medium (4 files)

### Task 5: Render the core recruiter-facing story

**Description:** Connect the local dataset and BLS output to the Streamlit page. The default
state should introduce the target and show the raw light curve, BLS periodogram, selected
candidate, and phase-folded transit without requiring visitor configuration.

**Acceptance criteria:**

- [ ] The default page tells a complete Observe → Search → Fold story.
- [ ] Charts use readable units, tooltips, consistent color semantics, and concise annotations.
- [ ] The page handles data or analysis errors with a useful message rather than a traceback.

**Verification:**

- [ ] `uv run pytest tests/test_app.py`
- [ ] Run `uv run streamlit run app.py` and manually inspect desktop and narrow layouts.

**Dependencies:** Task 4

**Files likely touched:**

- `pyproject.toml`
- `uv.lock`
- `src/transit_lab/charts.py`
- `app.py`
- `tests/test_app.py`

**Estimated scope:** Medium (5 files)

### Checkpoint B: Analytical proof

- [ ] Full test, lint, and type-check suite passes.
- [ ] A fresh clone can reproduce the BLS result from bundled data.
- [ ] A visitor can understand the target, candidate period, and folded transit in two minutes.
- [ ] Human review before adding method comparisons.

## Phase 2: Preparation and method-comparison story

### Task 6: Add signal-preparation views

**Description:** Package the notebook's raw, normalized, and detrended signals as explicit,
tested transformations. Expose their analytical consequences without presenting a new
denoising research contribution.

**Acceptance criteria:**

- [ ] Each preparation mode is deterministic and preserves aligned time/flux samples.
- [ ] Tests cover normalization scale, finite output, and detrending edge cases.
- [ ] The app explains what changed and why in one short sentence per mode.

**Verification:**

- [ ] `uv run pytest tests/test_analysis.py tests/test_app.py`
- [ ] Manually compare all preparation modes for stable chart axes and clear labels.

**Dependencies:** Tasks 3 and 5

**Files likely touched:**

- `src/transit_lab/analysis.py`
- `src/transit_lab/charts.py`
- `app.py`
- `tests/test_analysis.py`
- `tests/test_app.py`

**Estimated scope:** Medium (5 files)

### Task 7: Package the notebook's Fourier and SVD results

**Description:** Extract only the comparison outputs needed to explain why general frequency
methods can suggest misleading periods for box-shaped transit signals. Prefer versioned,
precomputed results when live SVD/Fourier work is slow, unstable, or visually unchanged.

**Acceptance criteria:**

- [ ] Fourier and SVD-assisted results are traceable to explicit notebook parameters.
- [ ] Their candidate periods and display series use the same units and comparison contract as BLS.
- [ ] Any precomputed artifact has a reproducible generation path and documented rationale.

**Verification:**

- [ ] `uv run pytest tests/test_comparisons.py`
- [ ] Recreate the packaged results once and compare them with the committed artifacts.

**Dependencies:** Task 6

**Files likely touched:**

- `src/transit_lab/comparisons.py`
- `data/demo/method_results.json`
- `tests/test_comparisons.py`
- `data/README.md`

**Estimated scope:** Medium (4 files)

### Task 8: Build the method comparison view

**Description:** Add a focused Compare step that lets visitors move between Fourier,
SVD-assisted, and BLS results while keeping the signal, axes, annotations, and interpretation
visually consistent.

**Acceptance criteria:**

- [ ] A bounded method selector updates the comparison without changing the underlying dataset.
- [ ] The UI makes the difference between “candidate signal” and “confirmed planet” explicit.
- [ ] BLS remains the recommended method for this signal shape, with a concise technical reason.

**Verification:**

- [ ] `uv run pytest tests/test_app.py`
- [ ] Manually inspect each method state and confirm the comparison is understandable without
  reading the notebook.

**Dependencies:** Task 7

**Files likely touched:**

- `src/transit_lab/charts.py`
- `app.py`
- `tests/test_app.py`

**Estimated scope:** Medium (3 files)

### Checkpoint C: Notebook analysis successfully repackaged

- [ ] Prepare and Compare steps work from the same versioned dataset.
- [ ] Fourier/SVD additions reuse prior work and introduce no unsupported scientific claims.
- [ ] Full quality suite passes and interaction remains responsive.
- [ ] Human review before final interaction and interpretation work.

## Phase 3: Interaction and interpretation

### Task 9: Add bounded candidate exploration and caching

**Description:** Let visitors choose among a few meaningful candidate periods and preparation
modes, then update the fold and evidence consistently. Cache static loading and expensive
serializable results with bounded keys so normal interaction feels immediate.

**Acceptance criteria:**

- [ ] Controls are limited to scientifically meaningful options and have stable widget keys.
- [ ] Candidate selection updates the folded chart and measurements together.
- [ ] Static loads and expensive computations are cached without unbounded parameter growth.

**Verification:**

- [ ] AppTest exercises every selectable candidate and preparation mode without exceptions.
- [ ] Manual rerun check confirms repeated selections do not redo expensive work unnecessarily.

**Dependencies:** Tasks 5 and 8

**Files likely touched:**

- `src/transit_lab/analysis.py`
- `src/transit_lab/charts.py`
- `app.py`
- `tests/test_app.py`

**Estimated scope:** Medium (4 files)

### Task 10: Add the evidence and limitations panel

**Description:** Present the selected period, approximate depth, duration, signal strength, and
reference comparison in a compact interpretation section. Explain uncertainty and validation
limits in recruiter-friendly language.

**Acceptance criteria:**

- [ ] Every displayed metric has a unit, definition, and traceable source or computation.
- [ ] Caveats distinguish transit-like evidence from planetary confirmation.
- [ ] “Under the hood” details use progressive disclosure and do not interrupt the main story.

**Verification:**

- [ ] Unit tests cover metric formatting and missing/invalid measurement handling.
- [ ] AppTest confirms the selected candidate and displayed evidence stay synchronized.

**Dependencies:** Tasks 4 and 9

**Files likely touched:**

- `src/transit_lab/presentation.py`
- `app.py`
- `tests/test_presentation.py`
- `tests/test_app.py`

**Estimated scope:** Medium (4 files)

### Checkpoint D: Portfolio MVP

- [ ] Observe → Prepare → Compare → Search → Fold → Interpret works end to end.
- [ ] Default state is complete; interaction deepens the story rather than unlocking it.
- [ ] No external service, upload, database, or authentication is required.
- [ ] Human approval that the MVP content and behavior are complete.

## Phase 4: Portfolio polish and launch readiness

### Task 11: Apply responsive visual and accessibility polish

**Description:** Refine hierarchy, spacing, copy, loading/error states, and chart composition
into the approved modern scientific-instrument aesthetic. Use the existing theme and native
Streamlit layout capabilities before considering CSS.

**Acceptance criteria:**

- [ ] The interface remains readable at desktop and narrow widths with no cramped metric grid.
- [ ] Color is not the only carrier of meaning; labels, contrast, and keyboard-usable widgets are clear.
- [ ] Loading, empty, and error states look intentional and preserve the analytical narrative.

**Verification:**

- [ ] Run the full automated quality suite.
- [ ] Complete a manual visual/accessibility pass at desktop and mobile-like widths.

**Dependencies:** Task 10

**Files likely touched:**

- `.streamlit/config.toml`
- `src/transit_lab/charts.py`
- `app.py`
- `tests/test_app.py`

**Estimated scope:** Medium (4 files)

### Task 12: Write the portfolio documentation

**Description:** Turn the scaffold README into a concise project case study covering the
problem, result, architecture, data provenance, methods, tradeoffs, limitations, local setup,
tests, and deployment link. Include one strong screenshot or short demo asset only if it helps
recruiters evaluate the project quickly.

**Acceptance criteria:**

- [ ] A new reader can run the app and understand the engineering decisions from the README.
- [ ] Data and scientific claims have direct attribution, and limitations are explicit.
- [ ] Repository links and media contain no machine-specific local paths.

**Verification:**

- [ ] Follow the README setup from a clean environment or fresh clone.
- [ ] Check every link and rendered Markdown section.

**Dependencies:** Tasks 10 and 11

**Files likely touched:**

- `README.md`
- `docs/architecture.md`
- `docs/assets/dashboard-preview.png`

**Estimated scope:** Medium (3 files)

### Task 13: Add a minimal continuous-integration gate

**Description:** Add one GitHub Actions workflow that installs the locked environment and runs
the same pytest, Ruff, and mypy checks used locally. Avoid release automation or a matrix unless
a real compatibility need appears.

**Acceptance criteria:**

- [ ] Pull requests and pushes to `main` run tests, linting, and type checking.
- [ ] The workflow uses the project's declared Python version and lockfile.
- [ ] CI configuration contains no credentials and duplicates no deployment workflow.

**Verification:**

- [ ] Validate the workflow syntax locally where possible.
- [ ] Confirm the first GitHub Actions run passes.

**Dependencies:** Task 5

**Files likely touched:**

- `.github/workflows/quality.yml`

**Estimated scope:** Small (1 file)

### Task 14: Deploy and perform the public-readiness audit

**Description:** Deploy the app to a simple Streamlit-compatible host using bundled data, then
audit the repository and deployed experience for secrets, absolute paths, broken links,
performance, and unsupported claims. Changing the GitHub repository from private to public is
a separate release action that requires explicit user approval at this checkpoint.

**Acceptance criteria:**

- [ ] The deployed default story loads without credentials or runtime network data access.
- [ ] Repository-wide scans find no secrets, local execution paths, or unintended personal data.
- [ ] The deployment URL, README, repository visibility, and release status match the user's
  explicit launch decision.

**Verification:**

- [ ] Smoke-test the deployed app in a fresh browser session at desktop and narrow widths.
- [ ] Run the full local quality suite and inspect the final staged/public diff.

**Dependencies:** Tasks 11, 12, and 13

**Files likely touched:**

- `README.md`
- `.streamlit/config.toml`
- Hosting configuration only if the selected platform requires it

**Estimated scope:** Small to medium (1-3 files plus external deployment state)

### Checkpoint E: Ready to share

- [ ] Hosted app and repository tell the same concise project story.
- [ ] CI is green and the release audit has no unresolved findings.
- [ ] User explicitly approves any repository visibility change.
- [ ] Portfolio project is ready to link from GitHub, a résumé, and applications.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| The notebook target or reference period is misidentified | High | Verify identity and reference values before building the data contract or public copy. |
| Notebook outputs expose local paths | High | Strip all outputs/counts first and enforce a path-regression test. |
| SVD work is slow or numerically brittle in a hosted app | Medium | Benchmark once; commit reproducible comparison artifacts unless live recomputation is clearly fast and useful. |
| Scientific dependencies make deployment heavy | Medium | Prefer direct Astropy/NumPy/SciPy functions; add Lightkurve only where it materially reduces code or preserves notebook behavior. |
| Interactions recompute the whole analysis | Medium | Cache immutable inputs/results and keep the candidate control set bounded. |
| The dashboard becomes dense or decorative | Medium | Keep one dominant analytical figure per step, concise copy, and no interaction without explanatory value. |
| Chart interactions are difficult to automate | Low | Use testable Streamlit widgets for state changes; reserve browser checks for actual rendering and responsiveness. |
| Dataset redistribution or attribution is unclear | Medium | Record source, license/usage terms, observation identifiers, and processing steps before launch. |

## Deferred ideas

- Multi-target browsing or live catalog search
- User-uploaded light curves
- Machine-learning classification
- New denoising research or transit validation
- Authentication, persistence, or a standalone API
- 3D scenes, mission-control decoration, or custom web components

## Decisions to revisit only at their checkpoint

- **After Task 7:** keep Fourier/SVD live only if measured runtime and stability justify it;
  otherwise use reproducible precomputed artifacts.
- **After Task 11:** decide whether one screenshot or a short demo clip materially improves the
  README.
- **After Task 14:** make the GitHub repository public only with explicit user approval.
