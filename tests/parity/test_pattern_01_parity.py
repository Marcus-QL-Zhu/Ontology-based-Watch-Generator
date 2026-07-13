from __future__ import annotations

import json
from pathlib import Path

from ontology_watch_generator.patterns.pattern_01_central_display import generate_pattern_01


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_pattern_01_public_artifacts_match_the_certified_baseline_inventory(tmp_path: Path) -> None:
    baseline = json.loads((REPOSITORY_ROOT / "reference_baselines" / "pattern_01.json").read_text(encoding="utf-8"))
    record = generate_pattern_01(731, tmp_path)
    published = json.loads((tmp_path / "current" / "MANIFEST.json").read_text(encoding="utf-8"))
    expected = {
        artifact["filename"]
        for artifact in baseline["artifacts"]
        if artifact["filename"] not in {"screenshots/pattern_01_top.png", "screenshots/pattern_01_isometric.png"}
        and not artifact["filename"].endswith(".glb")
    }
    expected.add(".watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step/model.glb")

    assert set(published["artifacts"]) == expected
    assert record.source_commit == baseline["source"]["commit"]
    assert published["run"]["design_id"] == "pattern1_seed_731_public"
