import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).parents[1]
DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "demo"
LIGHT_CURVE_PATH = DATA_DIRECTORY / "light_curve.csv"
METADATA_PATH = DATA_DIRECTORY / "target.json"
EXPECTED_COLUMNS = {
    "time_btjd",
    "sap_flux_e_per_s",
    "sap_flux_err_e_per_s",
    "normalized_flux",
    "normalized_flux_err",
}


def _load_metadata() -> dict[str, Any]:
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def test_demo_light_curve_is_finite_ordered_and_normalized() -> None:
    with LIGHT_CURVE_PATH.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        assert set(reader.fieldnames or ()) == EXPECTED_COLUMNS
        rows = list(reader)

    assert len(rows) > 1_000

    times = [float(row["time_btjd"]) for row in rows]
    normalized_flux = [float(row["normalized_flux"]) for row in rows]
    numeric_values = [float(value) for row in rows for value in row.values()]

    assert all(math.isfinite(value) for value in numeric_values)
    assert all(later > earlier for earlier, later in zip(times, times[1:], strict=False))
    assert math.isclose(statistics.median(normalized_flux), 1.0, abs_tol=1e-12)


def test_demo_metadata_identifies_the_verified_target_and_observation() -> None:
    metadata = _load_metadata()

    assert metadata["schema_version"] == "1.0"
    assert metadata["target"]["tic_id"] == 158324245
    assert metadata["target"]["toi"] == "TOI-1161.01"
    assert metadata["target"]["planet_name"] == "KOI-13 b"
    assert metadata["observation"]["mission"] == "TESS"
    assert metadata["observation"]["sector"] == 14
    assert metadata["observation"]["cadence_seconds"] == 120
    assert metadata["observation"]["runtime_network_required"] is False


def test_demo_metadata_records_processing_and_authoritative_sources() -> None:
    metadata = _load_metadata()

    assert metadata["processing"]["aperture"] == "SPOC pipeline aperture"
    assert metadata["processing"]["quality_mask"] == "Lightkurve default"
    assert metadata["reference_values"]["orbital_period_days"] == 1.7635881

    source_urls = {source["url"] for source in metadata["sources"]}
    assert any("exoplanetarchive.ipac.caltech.edu" in url for url in source_urls)
    assert any("archive.stsci.edu" in url for url in source_urls)


def test_demo_metadata_matches_the_bundled_csv() -> None:
    metadata = _load_metadata()
    csv_bytes = LIGHT_CURVE_PATH.read_bytes()
    with LIGHT_CURVE_PATH.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    processing = metadata["processing"]
    assert processing["csv_sha256"] == hashlib.sha256(csv_bytes).hexdigest()
    assert processing["row_count"] == len(rows)
    assert math.isclose(
        processing["time_start_btjd"],
        float(rows[0]["time_btjd"]),
        abs_tol=1e-12,
    )
    assert math.isclose(
        processing["time_end_btjd"],
        float(rows[-1]["time_btjd"]),
        abs_tol=1e-12,
    )
