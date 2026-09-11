"""Load the versioned offline dataset used by Transit Lab."""

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from transit_lab.models import LightCurve, TargetMetadata, TransitDataset

DEFAULT_DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "demo"
REQUIRED_COLUMNS = {
    "time_btjd",
    "sap_flux_e_per_s",
    "sap_flux_err_e_per_s",
    "normalized_flux",
    "normalized_flux_err",
}


class DataValidationError(ValueError):
    """Raised when bundled observations or metadata violate the data contract."""


def _load_light_curves(path: Path) -> tuple[LightCurve, LightCurve]:
    try:
        with path.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or ()))
            if missing:
                raise DataValidationError(
                    f"light curve CSV is missing required columns: {', '.join(missing)}"
                )

            rows = list(reader)
    except OSError as error:
        raise DataValidationError(f"unable to read light curve CSV: {error}") from error

    if not rows:
        raise DataValidationError("light curve CSV contains no observations")

    try:
        time = np.array([float(row["time_btjd"]) for row in rows], dtype=np.float64)
        raw_flux = np.array([float(row["sap_flux_e_per_s"]) for row in rows], dtype=np.float64)
        raw_flux_error = np.array(
            [float(row["sap_flux_err_e_per_s"]) for row in rows],
            dtype=np.float64,
        )
        normalized_flux = np.array(
            [float(row["normalized_flux"]) for row in rows],
            dtype=np.float64,
        )
        normalized_flux_error = np.array(
            [float(row["normalized_flux_err"]) for row in rows],
            dtype=np.float64,
        )
        return (
            LightCurve(time=time, flux=normalized_flux, flux_error=normalized_flux_error),
            LightCurve(time=time, flux=raw_flux, flux_error=raw_flux_error),
        )
    except (TypeError, ValueError) as error:
        raise DataValidationError(f"invalid light curve data: {error}") from error


def _load_target(path: Path) -> TargetMetadata:
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        target = payload["target"]
        observation = payload["observation"]
        reference = payload["reference_values"]

        return TargetMetadata(
            tic_id=int(target["tic_id"]),
            toi=str(target["toi"]),
            planet_name=str(target["planet_name"]),
            aliases=tuple(str(alias) for alias in target.get("aliases", ())),
            mission=str(observation["mission"]),
            sector=int(observation["sector"]),
            camera=int(observation["camera"]) if "camera" in observation else None,
            ccd=int(observation["ccd"]) if "ccd" in observation else None,
            cadence_seconds=int(observation["cadence_seconds"]),
            source_product=observation.get("source_product"),
            reference_period_days=float(reference["orbital_period_days"]),
            reference_transit_depth_ppm=(
                float(reference["transit_depth_ppm"])
                if "transit_depth_ppm" in reference
                else None
            ),
            reference_transit_duration_hours=(
                float(reference["transit_duration_hours"])
                if "transit_duration_hours" in reference
                else None
            ),
        )
    except OSError as error:
        raise DataValidationError(f"unable to read target metadata: {error}") from error
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise DataValidationError(
            f"target metadata has an invalid or missing required field: {error}"
        ) from error


def load_demo_dataset(directory: Path | None = None) -> TransitDataset:
    """Load and validate the repository's bundled demonstration dataset."""

    data_directory = directory or DEFAULT_DATA_DIRECTORY
    normalized_curve, raw_curve = _load_light_curves(data_directory / "light_curve.csv")
    return TransitDataset(
        light_curve=normalized_curve,
        raw_light_curve=raw_curve,
        target=_load_target(data_directory / "target.json"),
    )
