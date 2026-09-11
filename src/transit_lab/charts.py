"""Plotly figures for the Transit Lab analytical story."""

import numpy as np
import plotly.graph_objects as go
from numpy.typing import NDArray

from transit_lab.analysis import BLSResult, FoldedSignal
from transit_lab.comparisons import MethodComparison
from transit_lab.models import LightCurve

SIGNAL_COLOR = "#22AFC6"
CANDIDATE_COLOR = "#F2B84B"
MUTED_COLOR = "#A8B8CC"


def _apply_layout(figure: go.Figure, *, hovermode: str = "closest") -> go.Figure:
    figure.update_layout(
        height=380,
        margin={"l": 16, "r": 16, "t": 24, "b": 16},
        hovermode=hovermode,
        dragmode=False,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    figure.update_xaxes(showgrid=False, fixedrange=True)
    figure.update_yaxes(
        gridcolor="rgba(168, 184, 204, 0.16)",
        zeroline=False,
        fixedrange=True,
    )
    return figure


def build_light_curve_chart(
    curve: LightCurve,
    *,
    trace_name: str = "TESS observations",
    y_axis_title: str = "Normalized flux",
    hover_flux_label: str = "Normalized flux",
    hover_flux_format: str = ".6f",
) -> go.Figure:
    """Plot a complete TESS light curve with explicit signal units."""

    figure = go.Figure(
        go.Scattergl(
            x=curve.time,
            y=curve.flux,
            mode="markers",
            name=trace_name,
            marker={"color": SIGNAL_COLOR, "size": 3, "opacity": 0.55},
            hovertemplate=(
                f"BTJD %{{x:.4f}}<br>{hover_flux_label} "
                f"%{{y:{hover_flux_format}}}<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(title="Time (BTJD)")
    figure.update_yaxes(title=y_axis_title)
    return _apply_layout(figure)


def build_method_comparison_chart(
    comparison: MethodComparison,
    reference_period_days: float,
) -> go.Figure:
    """Plot one method on the shared normalized period-score scale."""

    candidate_index = int(np.argmax(comparison.score))
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=comparison.period_days,
            y=comparison.score,
            mode="lines",
            name=f"{comparison.label} score",
            line={"color": SIGNAL_COLOR, "width": 1.8},
            hovertemplate=(
                "Trial period %{x:.5f} days<br>Normalized score %{y:.3f}<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[comparison.candidate_period_days],
            y=[comparison.score[candidate_index]],
            mode="markers",
            name="Strongest candidate",
            marker={
                "color": CANDIDATE_COLOR,
                "size": 10,
                "line": {"color": "#07111F", "width": 1},
            },
            hovertemplate=(
                "Strongest candidate<br>Period %{x:.5f} days"
                "<br>Normalized score %{y:.3f}<extra></extra>"
            ),
        )
    )
    figure.add_vline(
        x=reference_period_days,
        line={"color": MUTED_COLOR, "dash": "dot", "width": 1.5},
        annotation_text="Archive period",
        annotation_position="top right",
    )
    figure.update_xaxes(title="Trial period (days)")
    figure.update_yaxes(title="Normalized method score", range=[0, 1.08])
    return _apply_layout(figure, hovermode="x")


def build_periodogram_chart(result: BLSResult, reference_period_days: float) -> go.Figure:
    """Plot BLS power and identify ranked candidate periods."""

    marker_sizes = [max(7, 11 - 2 * index) for index in range(len(result.candidates))]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=result.period_days,
            y=result.power,
            mode="lines",
            name="BLS power",
            line={"color": SIGNAL_COLOR, "width": 1.5},
            hovertemplate="Trial period %{x:.5f} days<br>Power %{y:.1f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[candidate.period_days for candidate in result.candidates],
            y=[candidate.power for candidate in result.candidates],
            mode="markers",
            name="Ranked candidates",
            marker={
                "color": CANDIDATE_COLOR,
                "size": marker_sizes,
                "line": {"color": "#07111F", "width": 1},
            },
            customdata=[
                [rank, candidate.depth_signal_to_noise]
                for rank, candidate in enumerate(result.candidates, start=1)
            ],
            hovertemplate=(
                "Candidate #%{customdata[0]}<br>Period %{x:.5f} days"
                "<br>Depth S/N %{customdata[1]:.1f}<extra></extra>"
            ),
        )
    )
    figure.add_vline(
        x=reference_period_days,
        line={"color": MUTED_COLOR, "dash": "dot", "width": 1.5},
        annotation_text="Archive period",
        annotation_position="top right",
    )
    figure.update_xaxes(title="Trial period (days)")
    figure.update_yaxes(title="BLS log-likelihood power")
    return _apply_layout(figure, hovermode="x")


def _bin_folded_curve(
    phase: NDArray[np.float64],
    flux: NDArray[np.float64],
    bin_count: int = 100,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    edges = np.linspace(-0.5, 0.5, bin_count + 1)
    bin_indices = np.clip(np.digitize(phase, edges) - 1, 0, bin_count - 1)
    centers = (edges[:-1] + edges[1:]) / 2
    medians = np.array(
        [np.median(flux[bin_indices == index]) for index in range(bin_count)],
        dtype=np.float64,
    )
    populated = np.isfinite(medians)
    return centers[populated], medians[populated]


def build_folded_chart(
    folded: FoldedSignal,
    *,
    trace_name: str = "Folded observations",
    y_axis_title: str = "Normalized flux",
    hover_flux_label: str = "Normalized flux",
    hover_flux_format: str = ".6f",
) -> go.Figure:
    """Plot observations folded around a selected candidate's transit center."""

    binned_phase, binned_flux = _bin_folded_curve(folded.phase, folded.flux)
    figure = go.Figure()
    figure.add_trace(
        go.Scattergl(
            x=folded.phase,
            y=folded.flux,
            mode="markers",
            name=trace_name,
            marker={"color": SIGNAL_COLOR, "size": 3, "opacity": 0.25},
            hovertemplate=(
                f"Phase %{{x:.4f}}<br>{hover_flux_label} "
                f"%{{y:{hover_flux_format}}}<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=binned_phase,
            y=binned_flux,
            mode="lines+markers",
            name="Binned median",
            line={"color": CANDIDATE_COLOR, "width": 2.5},
            marker={"color": CANDIDATE_COLOR, "size": 5},
            hovertemplate="Phase %{x:.4f}<br>Median flux %{y:.6f}<extra></extra>",
        )
    )
    figure.update_xaxes(title="Orbital phase", range=[-0.5, 0.5])
    figure.update_yaxes(title=y_axis_title)
    return _apply_layout(figure)
