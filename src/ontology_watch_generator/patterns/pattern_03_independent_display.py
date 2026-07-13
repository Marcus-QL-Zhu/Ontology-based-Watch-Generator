"""Exact public adapter for Pattern 3, backed by the former Pattern 4 entrypoint."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from ..core.run_record import RunRecord
from ..integrations.text_to_cad.publisher import derive_explorer_artifacts, publish_reference_run
from ..reference_backend.watch_kinematic import partitioned_bridge_stage


PATTERN_ID = "pattern-03"
SOURCE_MAP = Path(__file__).resolve().parents[1] / "reference_backend" / "SOURCE_MAP.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _frozen_source_commit() -> str:
    return json.loads(SOURCE_MAP.read_text(encoding="utf-8"))["frozen_source_commit"]


def generate_pattern_03(seed: int, output_dir: Path) -> RunRecord:
    """Generate public Pattern 3 via the frozen former Pattern 4 complete entrypoint."""

    with tempfile.TemporaryDirectory(prefix="ontology-watch-pattern-03-") as temp_dir:
        source_output = Path(temp_dir)
        result = partitioned_bridge_stage.build_pattern4_independent_display_complete_model(
            source_output,
            seed=seed,
            layout_id=f"pattern3_seed_{seed}_public",
            include_lightening=True,
        )
        if result.get("status") != "pass" or not result["generation_gate"]["allowed_to_open_or_deliver"]:
            raise RuntimeError("Pattern 3 reference backend did not pass its source hard gate")
        browser_artifacts = derive_explorer_artifacts(source_output, Path(result["artifacts"]["step"]))
        artifact_names = tuple(sorted({Path(value).name for value in result["artifacts"].values()} | set(browser_artifacts)))
        artifact_hashes = {name: _sha256(source_output / name) for name in artifact_names}
        record = RunRecord(
            pattern_id=PATTERN_ID,
            requested_seed=seed,
            resolved_seed=seed,
            source_commit=_frozen_source_commit(),
            backend_entrypoint="partitioned_bridge_stage.build_pattern4_independent_display_complete_model",
            design_id=result["layout_id"],
            required_artifacts=artifact_names,
            artifact_hashes=artifact_hashes,
        )
        publish_reference_run(record, source_output, output_dir)
        return record
