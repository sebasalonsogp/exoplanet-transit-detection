"""Streamlit entry point for the Transit Lab portfolio application."""

import streamlit as st

st.set_page_config(
    page_title="Transit Lab",
    page_icon=":material/planet:",
    layout="wide",
)

st.title("Transit Lab")
st.caption("An interactive workbench for finding planetary signals in noisy starlight.")

st.markdown(
    "Explore how signal preparation and method selection turn a raw TESS light curve "
    "into evidence for a transit-like candidate."
)
st.markdown("**Observe** → **Prepare** → **Compare** → **Search** → **Fold** → **Interpret**")

with st.container(border=True):
    st.header("Analysis workspace")
    st.write(
        "The application shell is ready. The first analytical slice will connect a verified "
        "local light curve to a reproducible Box Least Squares result."
    )
    st.caption("No remote services or scientific computations are included in this scaffold.")
