import numpy as np
import pytest

from transit_lab.models import LightCurve, TargetMetadata, TransitDataset


def test_light_curve_reports_observation_count() -> None:
    curve = LightCurve(
        time=np.array([1.0, 2.0, 3.0]),
        flux=np.array([1.0, 0.99, 1.01]),
    )

    assert curve.observation_count == 3


def test_light_curve_rejects_mismatched_sample_counts() -> None:
    with pytest.raises(ValueError, match="same number of samples"):
        LightCurve(
            time=np.array([1.0, 2.0]),
            flux=np.array([1.0]),
        )


@pytest.mark.parametrize(
    ("time", "flux", "message"),
    [
        (np.array([]), np.array([]), "at least one sample"),
        (np.array([1.0, np.nan]), np.array([1.0, 0.99]), "finite"),
        (np.array([1.0, 1.0]), np.array([1.0, 0.99]), "strictly increasing"),
    ],
)
def test_light_curve_rejects_invalid_observations(
    time: np.ndarray[tuple[int, ...], np.dtype[np.float64]],
    flux: np.ndarray[tuple[int, ...], np.dtype[np.float64]],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        LightCurve(time=time, flux=flux)


def test_light_curve_rejects_misaligned_uncertainties() -> None:
    with pytest.raises(ValueError, match="flux uncertainty"):
        LightCurve(
            time=np.array([1.0, 2.0]),
            flux=np.array([1.0, 0.99]),
            flux_error=np.array([0.01]),
        )


def test_transit_dataset_keeps_curve_and_target_together() -> None:
    curve = LightCurve(
        time=np.array([1.0, 2.0]),
        flux=np.array([1.0, 0.99]),
    )
    target = TargetMetadata(
        tic_id=158324245,
        toi="TOI-1161.01",
        planet_name="KOI-13 b",
        mission="TESS",
        sector=14,
        cadence_seconds=120,
        reference_period_days=1.7635881,
    )

    dataset = TransitDataset(light_curve=curve, raw_light_curve=curve, target=target)

    assert dataset.light_curve.observation_count == 2
    assert dataset.raw_light_curve.observation_count == 2
    assert dataset.target.planet_name == "KOI-13 b"
