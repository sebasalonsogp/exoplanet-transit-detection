"""Regenerate the versioned Fourier and SVD comparison artifact."""

import json
from pathlib import Path

from transit_lab import load_demo_dataset, prepare_signals
from transit_lab.comparisons import comparison_artifact_payload, generate_notebook_comparisons

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPOSITORY_ROOT / "data" / "demo" / "method_results.json"


def main() -> None:
    """Compute notebook-derived comparisons and write deterministic JSON."""

    dataset = load_demo_dataset()
    prepared = prepare_signals(dataset.raw_light_curve)
    results = generate_notebook_comparisons(prepared.detrended)
    payload = comparison_artifact_payload(results)
    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
