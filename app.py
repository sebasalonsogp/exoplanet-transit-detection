"""Streamlit entry point for the Transit Lab portfolio application."""

import streamlit as st

from transit_lab import BLSResult, DataValidationError, TransitDataset, load_demo_dataset, run_bls
from transit_lab.charts import (
    build_folded_chart,
    build_light_curve_chart,
    build_periodogram_chart,
)

st.set_page_config(
    page_title="Transit Lab",
    page_icon=":material/planet:",
    layout="wide",
)


@st.cache_data(show_spinner="Running the reproducible transit search…", max_entries=1)
def load_analysis() -> tuple[TransitDataset, BLSResult]:
    """Load the versioned observations and compute their default BLS result once."""

    dataset = load_demo_dataset()
    return dataset, run_bls(dataset.light_curve)


st.title("Transit Lab")
st.caption("An interactive workbench for finding planetary signals in noisy starlight.")

st.markdown(
    "Follow one verified TESS light curve from normalized observations to a reproducible "
    "transit-period candidate."
)
st.markdown("**Observe** → **Search** → **Fold**")

try:
    dataset, result = load_analysis()
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
    "The locally bundled light curve contains normalized brightness measurements from "
    "TESS. Individual dips are subtle when viewed across the full 27-day observation."
)
st.plotly_chart(
    build_light_curve_chart(dataset.light_curve),
    key="light-curve-chart",
    config={"displaylogo": False, "scrollZoom": False},
)

st.header("2. Search for repeating dips", icon=":material/search:")
st.write(
    "Box Least Squares tests box-shaped dimming events over periods from 1 to 10 days. "
    "The strongest peak lands on the known planet's orbital rhythm."
)
st.plotly_chart(
    build_periodogram_chart(result, target.reference_period_days),
    key="periodogram-chart",
    config={"displaylogo": False, "scrollZoom": False},
)
st.caption(
    f"Recovered period: {best.period_days:.5f} days · "
    f"NASA archive reference: {target.reference_period_days:.7f} days · "
    f"difference: {reference_difference_minutes:.1f} minutes"
)

st.header("3. Fold the strongest candidate", icon=":material/repeat:")
st.write(
    "Folding stacks every candidate orbit onto the same phase axis. The repeated dip near "
    "phase zero becomes clear in the amber median, while the individual measurements "
    "remain visible."
)
st.plotly_chart(
    build_folded_chart(result),
    key="folded-chart",
    config={"displaylogo": False, "scrollZoom": False},
)

with st.expander("Under the hood", icon=":material/code:"):
    st.write(
        "The app reads a versioned CSV—no live API call—then runs Astropy's Box Least Squares "
        "implementation with the class notebook's 0.1-day transit duration. The search uses "
        "6,489 trial periods between 1 and 10 days and ranks distinct local peaks."
    )
    st.caption(
        "BLS identifies a repeating transit-shaped signal; the external catalog provides the "
        "planet confirmation. Later phases will expose preparation and method comparisons."
    )
