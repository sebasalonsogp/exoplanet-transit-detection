"""Recruiter-facing formatting for transit-candidate evidence."""

from dataclasses import dataclass

import numpy as np

from transit_lab.analysis import TransitCandidate


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    """Display-ready measurements and interpretation for one BLS candidate."""

    period: str
    reference_offset: str
    depth: str
    duration: str
    depth_signal_to_noise: str
    interpretation: str


def format_depth_percent(depth_fraction: float | None) -> str:
    """Format a fractional transit depth as a percentage when valid."""

    if depth_fraction is None or not np.isfinite(depth_fraction) or depth_fraction < 0:
        return "Not available"
    return f"{depth_fraction * 100:.3f}%"


def format_duration_hours(duration_days: float | None) -> str:
    """Format a positive duration in days as hours when valid."""

    if duration_days is None or not np.isfinite(duration_days) or duration_days <= 0:
        return "Not available"
    return f"{duration_days * 24:.2f} hours"


def format_signal_to_noise(depth_signal_to_noise: float | None) -> str:
    """Format a nonnegative dimensionless depth signal-to-noise value."""

    if (
        depth_signal_to_noise is None
        or not np.isfinite(depth_signal_to_noise)
        or depth_signal_to_noise < 0
    ):
        return "Not available"
    return f"{depth_signal_to_noise:.1f}"


def _format_reference_offset(period_days: float, reference_period_days: float) -> str:
    difference_days = abs(period_days - reference_period_days)
    difference_minutes = difference_days * 24 * 60
    if difference_minutes < 60:
        return f"{difference_minutes:.1f} min from archive"
    if difference_days < 1:
        return f"{difference_days * 24:.1f} hours from archive"
    return f"{difference_days:.3f} days from archive"


def _interpret_period(
    period_days: float,
    reference_period_days: float,
    rank: int,
) -> str:
    difference_minutes = abs(period_days - reference_period_days) * 24 * 60
    if difference_minutes < 15:
        return (
            f"Candidate #{rank} is {difference_minutes:.1f} minutes from the archive period, "
            "so the detected rhythm closely agrees with the external reference."
        )

    ratio = period_days / reference_period_days
    nearest_multiple = round(ratio)
    if nearest_multiple >= 2 and abs(ratio - nearest_multiple) < 0.01:
        return (
            f"Candidate #{rank} is approximately {nearest_multiple}× the archive period—an "
            "integer multiple of the same repeating signal, not independent confirmation."
        )
    return (
        f"Candidate #{rank} does not closely match the archive period and should be treated "
        "as an alternate signal hypothesis."
    )


def build_candidate_evidence(
    candidate: TransitCandidate,
    *,
    reference_period_days: float,
    rank: int,
) -> CandidateEvidence:
    """Create display values and a bounded interpretation for one candidate."""

    if not np.isfinite(candidate.period_days) or candidate.period_days <= 0:
        raise ValueError("candidate period must be a positive finite number")
    if not np.isfinite(reference_period_days) or reference_period_days <= 0:
        raise ValueError("reference period must be a positive finite number")
    if rank <= 0:
        raise ValueError("candidate rank must be positive")

    return CandidateEvidence(
        period=f"{candidate.period_days:.5f} days",
        reference_offset=_format_reference_offset(
            candidate.period_days,
            reference_period_days,
        ),
        depth=format_depth_percent(candidate.depth_fraction),
        duration=format_duration_hours(candidate.duration_days),
        depth_signal_to_noise=format_signal_to_noise(candidate.depth_signal_to_noise),
        interpretation=_interpret_period(
            candidate.period_days,
            reference_period_days,
            rank,
        ),
    )
