from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from ontology_watch_generator.patterns.pattern_02_separate_serial_display import generate_pattern_02


def test_reference_backend_forces_a_headless_matplotlib_backend() -> None:
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "TkAgg"
    source_root = Path(__file__).resolve().parents[2] / "src"
    environment["PYTHONPATH"] = os.pathsep.join(
        item for item in (str(source_root), environment.get("PYTHONPATH", "")) if item
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import matplotlib; "
                "import ontology_watch_generator.reference_backend.watch_kinematic; "
                "print(matplotlib.get_backend())"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.stdout.strip().lower() == "agg"


def test_pattern_02_generation_publishes_checklist_and_complete_bridge_model(tmp_path: Path) -> None:
    record = generate_pattern_02(8459, tmp_path)
    current = tmp_path / "current"
    manifest = json.loads((current / "MANIFEST.json").read_text(encoding="utf-8"))

    assert record.pattern_id == "pattern-02"
    assert record.requested_seed == record.resolved_seed == 8459
    assert (current / "checklist.json").is_file()
    assert (current / "checklist.html").is_file()
    assert (current / "watch_power_chain_separate_display_with_analytic_partitioned_bridges.step").is_file()
    assert (current / ".watch_power_chain_separate_display_with_analytic_partitioned_bridges.step" / "model.glb").is_file()
    assert record.artifact_hashes == {name: item["sha256"] for name, item in manifest["artifacts"].items()}
