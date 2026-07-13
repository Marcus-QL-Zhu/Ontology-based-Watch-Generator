from __future__ import annotations

import json
from pathlib import Path

from ontology_watch_generator.patterns.pattern_03_independent_display import generate_pattern_03


def test_pattern_03_generation_publishes_hard_gated_complete_model(tmp_path: Path) -> None:
    record = generate_pattern_03(731, tmp_path)
    current = tmp_path / "current"
    report = json.loads((current / "pattern4_independent_display_complete_model_report.json").read_text(encoding="utf-8"))

    assert record.pattern_id == "pattern-03"
    assert record.requested_seed == record.resolved_seed == 731
    assert report["status"] == "pass"
    assert report["generation_gate"]["allowed_to_open_or_deliver"] is True
    assert set(report["evidence"]) == {"solver", "semantic", "role_contracts", "kinematic"}
    assert (current / ".watch_power_chain_pattern4_independent_display_with_analytic_partitioned_bridges.step" / "model.glb").is_file()
