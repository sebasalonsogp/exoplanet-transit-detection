"""Core contracts and analysis utilities for Transit Lab."""

from transit_lab.analysis import BLSConfig, BLSResult, TransitCandidate, run_bls
from transit_lab.data import DataValidationError, load_demo_dataset
from transit_lab.models import LightCurve, TargetMetadata, TransitDataset

__all__ = [
    "DataValidationError",
    "BLSConfig",
    "BLSResult",
    "LightCurve",
    "TargetMetadata",
    "TransitCandidate",
    "TransitDataset",
    "load_demo_dataset",
    "run_bls",
]
