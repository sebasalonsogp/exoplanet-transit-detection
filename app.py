"""Streamlit entry point for the Transit Lab portfolio application."""

import streamlit as st

from transit_lab import (
    BLSResult,
    DataValidationError,
    MethodComparison,
    PreparedSignals,
    TransitDataset,
    build_bls_comparison,
    load_demo_dataset,
    load_packaged_comparisons,
    prepare_signals,
    run_bls,
)
from transit_lab.charts import (
    build_folded_chart,
    build_light_curve_chart,
    build_method_comparison_chart,
    build_periodogram_chart,
)

PLOTLY_CONFIG = {"displaylogo": False, "displayModeBar": False, "scrollZoom": False}

st.set_page_config(
    page_title="Transit Lab",
    page_icon=":material/planet:",
    layout="wide",
)


@st.cache_data(show_spinner="Running the reproducible transit search…", max_entries=1)
def load_analysis() -> tuple[
    TransitDataset,
    PreparedSignals,
    BLSResult,
    dict[str, MethodComparison],
]:
    """Load one observation and its cached preparation and comparison results."""

    dataset = load_demo_dataset()
    prepared = prepare_signals(dataset.raw_light_curve)
    result = run_bls(dataset.light_curve)
    comparisons = load_packaged_comparisons()
    comparisons["bls"] = build_bls_comparison(result)
    return dataset, prepared, result, comparisons


st.title("Transit Lab")
st.caption("An interactive workbench for finding planetary signals in noisy starlight.")

st.markdown(
    "Follow one verified TESS light curve from raw observations to a reproducible "
    "transit-period candidate."
)
st.markdown("**Observe** → **Prepare** → **Compare** → **Search** → **Fold**")

try:
    dataset, prepared, result, comparisons = load_analysis()
except (DataValidationError, ValueError) as error:
    st.error(
        "Transit Lab could not load the bundled analysis. "
        "Check the versioned data files and analysis configuration.",
        icon=":material/error:",
    )
    st.caption(f"Technical detail: {error}")
    st.stop()

target = dataset.target
best = result.best_candidate
reference_difference_minutes = abs(best.period_days - target.reference_period_days) * 24 * 60

with st.container(horizontal=True, vertical_alignment="center"):
    st.badge("Offline and reproducible", icon=":material/database:", color="blue")
    st.caption(f"{target.mission} Sector {target.sector} · {target.toi} · 120-second cadence")

with st.container(horizontal=True):
    st.metric("Target", target.planet_name, icon=":material/planet:", border=True)
    st.metric(
        "Observations",
        f"{dataset.light_curve.observation_count:,}",
        icon=":material/scatter_plot:",
        border=True,
    )
    st.metric(
        "Best BLS period",
        f"{best.period_days:.5f} days",
        help="Strongest period from the Box Least Squares search.",
        icon=":material/timeline:",
        border=True,
    )
    st.metric(
        "Depth signal-to-noise",
        f"{best.depth_signal_to_noise:.1f}",
        help="Estimated transit depth divided by its uncertainty.",
        icon=":material/query_stats:",
        border=True,
    )

st.header("1. Observe the stellar signal", icon=":material/visibility:")
st.write(
    "The locally bundled light curve starts with TESS simple-aperture photometry. Individual "
    "dips are subtle when viewed across the full 27-day observation."
)
st.plotly_chart(
    build_light_curve_chart(
        prepared.raw,
        trace_name="Raw SAP flux",
        y_axis_title="SAP flux (electrons/second)",
        hover_flux_label="SAP flux",
        hover_flux_format=",.0f",
    ),
    key="raw-light-curve-chart",
    config=PLOTLY_CONFIG,
)

st.header("2. Prepare the signal", icon=":material/tune:")
st.write(
    "Move through the same observations as they are scaled and detrended for analysis. "
    "The default shows the prepared signal used by the Fourier and SVD comparisons."
)
preparation_mode = st.segmented_control(
    "Signal preparation",
    options=["Raw", "Normalized", "Detrended"],
    default="Detrended",
    key="preparation-mode",
    selection_mode="single",
    required=True,
    width="stretch",
)
if preparation_mode == "Raw":
    prepared_curve = prepared.raw
    preparation_explanation = (
        "Raw preserves detector measurements in instrument units before scaling."
    )
    preparation_chart = build_light_curve_chart(
        prepared_curve,
        trace_name="Raw SAP flux",
        y_axis_title="SAP flux (electrons/second)",
        hover_flux_label="SAP flux",
        hover_flux_format=",.0f",
    )
elif preparation_mode == "Normalized":
    prepared_curve = prepared.normalized
    preparation_explanation = (
        "Normalized divides by the median so the median brightness equals one."
    )
    preparation_chart = build_light_curve_chart(
        prepared_curve,
        trace_name="Normalized flux",
    )
else:
    prepared_curve = prepared.detrended
    preparation_explanation = (
        "Detrended divides out slow baseline changes using the notebook's local "
        "Savitzky–Golay settings."
    )
    preparation_chart = build_light_curve_chart(
        prepared_curve,
        trace_name="Detrended flux",
        y_axis_title="Detrended normalized flux",
        hover_flux_label="Detrended flux",
    )
st.write(preparation_explanation)
st.plotly_chart(
    preparation_chart,
    key="prepared-light-curve-chart",
    config=PLOTLY_CONFIG,
)

st.header("3. Compare detection methods", icon=":material/compare_arrows:")
st.write(
    "The notebook's Fourier and SVD-assisted approaches sit beside Box Least Squares on one "
    "normalized score scale. Each curve comes from the same versioned TESS observation."
)
with st.container(horizontal=True):
    st.metric(
        "Fourier candidate",
        f"{comparisons['fourier'].candidate_period_days:.5f} days",
        border=True,
    )
    st.metric(
        "SVD + Fourier candidate",
        f"{comparisons['svd_fourier'].candidate_period_days:.5f} days",
        border=True,
    )
    st.metric(
        "BLS candidate",
        f"{comparisons['bls'].candidate_period_days:.5f} days",
        border=True,
    )

method_by_label = {comparison.label: comparison for comparison in comparisons.values()}
method_label = st.segmented_control(
    "Detection method",
    options=["Fourier transform", "SVD-assisted Fourier", "Box Least Squares"],
    default="Box Least Squares",
    key="comparison-method",
    selection_mode="single",
    required=True,
    width="stretch",
)
if method_label is None:
    st.stop()
selected_comparison = method_by_label[method_label]
with st.container(horizontal=True, vertical_alignment="center"):
    if selected_comparison.recommended:
        st.badge("Recommended for transit-shaped dips", color="green")
    else:
        st.badge("Comparison method", color="gray")
    st.caption(selected_comparison.parameter_summary)
st.write(selected_comparison.interpretation)
st.plotly_chart(
    build_method_comparison_chart(selected_comparison, target.reference_period_days),
    key="method-comparison-chart",
    config=PLOTLY_CONFIG,
)
st.markdown(
    "Each peak is a **candidate signal**, not a planet confirmation. Confirmation comes from "
    "external catalog evidence; BLS is recommended here because a box-shaped model matches "
    "short, flat-bottomed transit dips directly."
)

st.header("4. Search for repeating dips", icon=":material/search:")
st.write(
    "Box Least Squares tests box-shaped dimming events over periods from 1 to 10 days. "
    "The detailed likelihood view preserves the full search scale, and its strongest peak "
    "lands on the known planet's orbital rhythm."
)
st.plotly_chart(
    build_periodogram_chart(result, target.reference_period_days),
    key="periodogram-chart",
    config=PLOTLY_CONFIG,
)
st.caption(
    f"Recovered period: {best.period_days:.5f} days · "
    f"NASA archive reference: {target.reference_period_days:.7f} days · "
    f"difference: {reference_difference_minutes:.1f} minutes"
)

st.header("5. Fold the strongest candidate", icon=":material/repeat:")
st.write(
    "Folding stacks every candidate orbit onto the same phase axis. The repeated dip near "
    "phase zero becomes clear in the amber median, while the individual measurements "
    "remain visible."
)
st.plotly_chart(
    build_folded_chart(result),
    key="folded-chart",
    config=PLOTLY_CONFIG,
)

with st.expander("Under the hood", icon=":material/code:"):
    st.write(
        "The app reads a versioned CSV—no live API call—prepares aligned signal views, loads "
        "reproducible notebook-method artifacts, and runs Astropy's Box Least Squares with "
        "the class notebook's 0.1-day transit duration."
    )
    st.caption(
        "The BLS search evaluates 6,489 trial periods between 1 and 10 days and ranks distinct "
        "local peaks. BLS identifies a repeating transit-shaped signal; the external catalog "
        "provides the planet confirmation."
    )
