"""Exact public adapter for Pattern 2: separate hour/minute serial display."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from ..core.run_record import RunRecord
from ..integrations.text_to_cad.publisher import derive_explorer_artifacts, publish_reference_run
from ..reference_backend.watch_kinematic import partitioned_bridge_stage, pattern_card_checklist, power_chain_mvp
from ..reference_backend.watch_kinematic.pattern_cards.separate_hour_minute_no_seconds import PATTERN_CARD_ID


PATTERN_ID = "pattern-02"
SOURCE_MAP = Path(__file__).resolve().parents[1] / "reference_backend" / "SOURCE_MAP.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _frozen_source_commit() -> str:
    return json.loads(SOURCE_MAP.read_text(encoding="utf-8"))["frozen_source_commit"]


def generate_pattern_02(seed: int, output_dir: Path) -> RunRecord:
    """Generate Pattern 2 through its frozen source chain and atomically publish it."""

    with tempfile.TemporaryDirectory(prefix="ontology-watch-pattern-02-") as temp_dir:
        source_output = Path(temp_dir)
        base = power_chain_mvp.run_power_chain_mvp(source_output, seed=seed, pattern_card_id=PATTERN_CARD_ID)
        final = partitioned_bridge_stage.build_separate_display_partitioned_bridge_stage(
            source_output,
            seed=seed,
            layout_id=f"pattern2_seed_{seed}_public",
            include_lightening=True,
        )
        checklist = pattern_card_checklist.write_pattern2_checklist_artifacts(source_output, seed=seed)
        if any(result.get("status") != "pass" for result in (base, final, checklist)):
            raise RuntimeError("Pattern 2 reference backend did not pass its source gate")
        browser_artifacts = derive_explorer_artifacts(source_output, Path(final["artifacts"]["step"]))
        artifact_names = tuple(sorted({
            Path(value).name
            for result in (base, final, checklist)
            for value in result["artifacts"].values()
        } | set(browser_artifacts)))
        artifact_hashes = {name: _sha256(source_output / name) for name in artifact_names}
        record = RunRecord(
            pattern_id=PATTERN_ID,
            requested_seed=seed,
            resolved_seed=seed,
            source_commit=_frozen_source_commit(),
            backend_entrypoint=(
                "power_chain_mvp.run_power_chain_mvp + "
                "partitioned_bridge_stage.build_separate_display_partitioned_bridge_stage + "
                "pattern_card_checklist.write_pattern2_checklist_artifacts"
            ),
            design_id=final["layout_id"],
            required_artifacts=artifact_names,
            artifact_hashes=artifact_hashes,
        )
        publish_reference_run(record, source_output, output_dir)
        return record
