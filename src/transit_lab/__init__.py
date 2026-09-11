"""Core contracts and analysis utilities for Transit Lab."""

from transit_lab.data import DataValidationError, load_demo_dataset
from transit_lab.models import LightCurve, TargetMetadata, TransitDataset

__all__ = [
    "DataValidationError",
    "LightCurve",
    "TargetMetadata",
    "TransitDataset",
    "load_demo_dataset",
]
