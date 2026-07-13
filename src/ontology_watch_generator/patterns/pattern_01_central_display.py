"""Exact public adapter for Pattern 1: central hour/minute with off-center seconds."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from ..core.run_record import RunRecord
from ..integrations.text_to_cad.publisher import derive_explorer_artifacts, publish_reference_run
from ..reference_backend.watch_kinematic import partitioned_bridge_stage, power_chain_mvp


PATTERN_ID = "pattern-01"
SOURCE_MAP = Path(__file__).resolve().parents[1] / "reference_backend" / "SOURCE_MAP.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _frozen_source_commit() -> str:
    return json.loads(SOURCE_MAP.read_text(encoding="utf-8"))["frozen_source_commit"]


def generate_pattern_01(seed: int, output_dir: Path) -> RunRecord:
    """Generate Pattern 1 through the frozen source chain and atomically publish it."""

    with tempfile.TemporaryDirectory(prefix="ontology-watch-pattern-01-") as temp_dir:
        source_output = Path(temp_dir)
        base = power_chain_mvp.run_power_chain_mvp(source_output, seed=seed)
        final = partitioned_bridge_stage.build_partitioned_bridge_stage(
            source_output,
            seed=seed,
            layout_id=f"pattern1_seed_{seed}_public",
            include_lightening=True,
        )
        if base.get("status") != "pass" or final.get("status") != "pass":
            raise RuntimeError("Pattern 1 reference backend did not pass its source gate")
        browser_artifacts = derive_explorer_artifacts(source_output, Path(final["artifacts"]["step"]))
        artifact_names = tuple(sorted({
            Path(value).name
            for result in (base, final)
            for value in result["artifacts"].values()
        } | set(browser_artifacts)))
        artifact_hashes = {name: _sha256(source_output / name) for name in artifact_names}
        record = RunRecord(
            pattern_id=PATTERN_ID,
            requested_seed=seed,
            resolved_seed=seed,
            source_commit=_frozen_source_commit(),
            backend_entrypoint="power_chain_mvp.run_power_chain_mvp + partitioned_bridge_stage.build_partitioned_bridge_stage",
            design_id=final["layout_id"],
            required_artifacts=artifact_names,
            artifact_hashes=artifact_hashes,
        )
        publish_reference_run(record, source_output, output_dir)
        return record
