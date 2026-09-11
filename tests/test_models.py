import numpy as np
import pytest

from transit_lab.models import LightCurve


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
