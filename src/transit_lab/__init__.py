"""Core contracts and analysis utilities for Transit Lab."""

from transit_lab.analysis import (
    BLSConfig,
    BLSResult,
    DetrendConfig,
    PreparedSignals,
    TransitCandidate,
    detrend_light_curve,
    normalize_light_curve,
    prepare_signals,
    run_bls,
)
from transit_lab.data import DataValidationError, load_demo_dataset
from transit_lab.models import LightCurve, TargetMetadata, TransitDataset

__all__ = [
    "DataValidationError",
    "BLSConfig",
    "BLSResult",
    "DetrendConfig",
    "LightCurve",
    "PreparedSignals",
    "TargetMetadata",
    "TransitCandidate",
    "TransitDataset",
    "detrend_light_curve",
    "load_demo_dataset",
    "normalize_light_curve",
    "prepare_signals",
    "run_bls",
]
