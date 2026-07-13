from __future__ import annotations

import json
from pathlib import Path

from ontology_watch_generator.patterns.pattern_01_central_display import generate_pattern_01


def test_pattern_01_generation_publishes_the_complete_source_artifact_set(tmp_path: Path) -> None:
    record = generate_pattern_01(731, tmp_path)
    current = tmp_path / "current"
    manifest = json.loads((current / "MANIFEST.json").read_text(encoding="utf-8"))

    assert record.pattern_id == "pattern-01"
    assert record.requested_seed == record.resolved_seed == 731
    assert record.artifact_hashes == {name: item["sha256"] for name, item in manifest["artifacts"].items()}
    assert (current / "watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step").is_file()
    assert (current / ".watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step.js").is_file()
    assert (
        current
        / ".watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step"
        / "model.glb"
    ).is_file()
