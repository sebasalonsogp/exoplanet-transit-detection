# Demo data

This directory contains the small, analysis-ready dataset used by the public application.
The app reads these versioned files locally and makes no runtime request to NASA or MAST.

## Target and observation

- **Target:** TIC 158324245 / TOI-1161.01
- **Known planet:** KOI-13 b, also called Kepler-13 b or TOI-1161 b
- **Observation:** TESS Sector 14, Camera 2, CCD 3
- **Cadence:** 120 seconds
- **Source product:** SPOC Target Pixel File
  `tess2019198215352-s0014-0000000158324245-0150-s_tp.fits`

The original class notebook searches for TOI 1161 and downloads this Sector 14 target pixel
file. NASA's Exoplanet Archive confirms that TIC 158324245 corresponds to the KOI-13 system;
the notebook's TOI and KOI labels therefore refer to the same target rather than two objects.

## Bundled files

- `demo/light_curve.csv` contains 18,420 finite, time-ordered observations. It includes the
  simple aperture photometry (SAP) flux, its uncertainty, and median-normalized equivalents.
- `demo/target.json` records identifiers, observation context, column definitions, processing
  steps, checksums, reference values, queries, and source URLs.
- `demo/method_results.json` stores deterministic Fourier and SVD-assisted period scores
  regenerated from the bundled curve. Keeping this compact artifact in version control makes
  the dashboard fast and reproducible without rerunning the notebook on every page load.

`time_btjd` uses BTJD, defined as BJD minus 2,457,000 days. Raw flux values are electrons per
second. `normalized_flux` is dimensionless and has a median of one.

## Extraction and processing

The CSV was exported once with Lightkurve 2.6.0 using the same core path as the notebook:

1. Search MAST for TIC 158324245, TESS Sector 14, SPOC, 120-second Target Pixel Files.
2. Download the single matching product with Lightkurve's default quality mask.
3. Sum the pixels selected by the SPOC pipeline aperture to obtain SAP flux.
4. Remove samples with non-finite time, flux, or flux uncertainty and sort by time.
5. Divide flux and uncertainty by the median SAP flux.

No detrending or period search is baked into the dataset. Those transformations belong to the
tested analysis layer so the application can show their effects explicitly.

## Notebook-method comparison

Phase 2 repackages two exploratory methods from `assets/astro.ipynb` rather than introducing
new scientific analysis. Both use the app's Savitzky-Golay-detrended normalized flux and the
notebook's bounded settings:

- Fourier: real FFT, restricted to candidate periods from 1 to 10 days.
- SVD-assisted Fourier: overlapping 50-sample windows, rank-6 reconstruction, then a real FFT
  of the reconstruction residual over the same period range.

The notebook's experimental L1 optimizer is intentionally omitted: it is computationally
expensive, its notebook outputs were not retained, and reproducing or tuning it would add new
scientific work outside this portfolio project's scope. Box Least Squares remains the primary
method because its box-shaped model fits transit-like dips directly.

Regenerate the packaged comparison after changing the preparation pipeline with:

```powershell
uv run python scripts/generate_method_results.py
```

The test suite verifies that the packaged values match a fresh computation.

## Reference values

The NASA Exoplanet Archive's TESS Project Candidates row reports:

| Field | Value |
| --- | ---: |
| Disposition | KP (known planet) |
| Orbital period | 1.7635881 days |
| Transit depth | 6,650 ppm |
| Transit duration | 3.092 hours |

The archive's composite confirmed-planet row reports a nearly identical period of 1.763588
days but a depth of 0.45906% and duration of 3.16877 hours. These tables compile different
source values and update on different schedules. The project therefore uses the period as a
validation reference while presenting depth and duration as approximate measurements from the
selected light curve.

## Provenance and use

- [MAST source Target Pixel File](https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:TESS/product/tess2019198215352-s0014-0000000158324245-0150-s_tp.fits)
- [MAST TESS data products](https://archive.stsci.edu/missions-and-data/tess/data-products)
- [NASA Exoplanet Archive TAP documentation](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)
- [NASA Exoplanet Archive TOI column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_TOI_columns.html)
- [NASA Exoplanet Archive KOI-13 overview](https://exoplanetarchive.ipac.caltech.edu/overview/KOI-13)
- [Lightkurve target-pixel-file search](https://lightkurve.github.io/lightkurve/reference/api/lightkurve.search_targetpixelfile.html)
- [Lightkurve normalization](https://lightkurve.github.io/lightkurve/reference/api/lightkurve.LightCurve.normalize.html)
- [MAST data use policy](https://archive.stsci.edu/publishing/data-use)

MAST states that most hosted data are in the public domain and asks users to acknowledge the
originating mission and STScI. This project attributes TESS, NASA, MAST/STScI, SPOC, and the
NASA Exoplanet Archive accordingly.
