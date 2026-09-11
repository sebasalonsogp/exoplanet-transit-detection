import csv
import json
from pathlib import Path

import pytest

from transit_lab.data import DataValidationError, load_demo_dataset
from transit_lab.models import LightCurve, TargetMetadata, TransitDataset


def _write_metadata(directory: Path) -> None:
    metadata = {
        "target": {
            "tic_id": 158324245,
            "toi": "TOI-1161.01",
            "planet_name": "KOI-13 b",
        },
        "observation": {
            "mission": "TESS",
            "sector": 14,
            "cadence_seconds": 120,
        },
        "reference_values": {"orbital_period_days": 1.7635881},
    }
    (directory / "target.json").write_text(json.dumps(metadata), encoding="utf-8")


def _write_curve(directory: Path, rows: list[dict[str, str]]) -> None:
    with (directory / "light_curve.csv").open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_load_demo_dataset_returns_typed_offline_data() -> None:
    dataset = load_demo_dataset()

    assert isinstance(dataset, TransitDataset)
    assert isinstance(dataset.light_curve, LightCurve)
    assert isinstance(dataset.raw_light_curve, LightCurve)
    assert isinstance(dataset.target, TargetMetadata)
    assert dataset.light_curve.observation_count == 18_420
    assert dataset.raw_light_curve.observation_count == 18_420
    assert dataset.raw_light_curve.flux.shape == dataset.light_curve.flux.shape
    assert dataset.raw_light_curve.flux.mean() > 10_000
    assert dataset.target.tic_id == 158324245
    assert dataset.target.reference_period_days == pytest.approx(1.7635881)


def test_load_demo_dataset_reports_missing_columns(tmp_path: Path) -> None:
    _write_metadata(tmp_path)
    _write_curve(
        tmp_path,
        [
            {
                "time_btjd": "1.0",
                "sap_flux_e_per_s": "100.0",
                "sap_flux_err_e_per_s": "1.0",
                "normalized_flux": "1.0",
            }
        ],
    )

    with pytest.raises(DataValidationError, match="missing required columns.*normalized_flux_err"):
        load_demo_dataset(tmp_path)


def test_load_demo_dataset_reports_empty_csv(tmp_path: Path) -> None:
    _write_metadata(tmp_path)
    (tmp_path / "light_curve.csv").write_text(
        (
            "time_btjd,sap_flux_e_per_s,sap_flux_err_e_per_s,"
            "normalized_flux,normalized_flux_err\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(DataValidationError, match="contains no observations"):
        load_demo_dataset(tmp_path)


def test_load_demo_dataset_reports_non_finite_values(tmp_path: Path) -> None:
    _write_metadata(tmp_path)
    _write_curve(
        tmp_path,
        [
            {
                "time_btjd": "1.0",
                "sap_flux_e_per_s": "100.0",
                "sap_flux_err_e_per_s": "1.0",
                "normalized_flux": "nan",
                "normalized_flux_err": "0.01",
            }
        ],
    )

    with pytest.raises(DataValidationError, match="finite"):
        load_demo_dataset(tmp_path)


def test_load_demo_dataset_reports_missing_metadata(tmp_path: Path) -> None:
    _write_curve(
        tmp_path,
        [
            {
                "time_btjd": "1.0",
                "sap_flux_e_per_s": "100.0",
                "sap_flux_err_e_per_s": "1.0",
                "normalized_flux": "1.0",
                "normalized_flux_err": "0.01",
            }
        ],
    )
    (tmp_path / "target.json").write_text("{}", encoding="utf-8")

    with pytest.raises(DataValidationError, match="missing required field"):
        load_demo_dataset(tmp_path)
