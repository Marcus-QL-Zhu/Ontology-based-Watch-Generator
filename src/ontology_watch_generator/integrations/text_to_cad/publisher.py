"""Publish an already-generated reference run without touching its geometry."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path

from ...core.artifacts import is_semantic_or_motion_artifact
from ...core.run_record import RunRecord
from .explorer_artifacts.transcode import generate_explorer_artifacts


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def derive_explorer_artifacts(source_output_dir: Path, step_path: Path) -> tuple[str, ...]:
    """Create and name browser artifacts derived from the same-run final STEP."""

    source_root = source_output_dir.resolve()
    derived = generate_explorer_artifacts(step_path)
    return tuple(path.resolve().relative_to(source_root).as_posix() for path in derived)


def _validate_run_record(run_record: RunRecord) -> None:
    if run_record.requested_seed != run_record.resolved_seed:
        raise ValueError("requested and resolved seed must match before publication")
    if not run_record.required_artifacts:
        raise ValueError("a run record must declare its required artifacts")
    if len(set(run_record.required_artifacts)) != len(run_record.required_artifacts):
        raise ValueError("a run record cannot declare an artifact twice")
    for artifact in run_record.required_artifacts:
        candidate = Path(artifact)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("artifact paths must be relative and remain inside the run directory")


def publish_reference_run(run_record: RunRecord, source_output_dir: Path, destination_dir: Path) -> Path:
    """Atomically publish a known backend output under ``destination_dir/current``."""

    _validate_run_record(run_record)
    source_output_dir = source_output_dir.resolve()
    destination_dir = destination_dir.resolve()
    if not source_output_dir.is_dir():
        raise ValueError(f"reference output directory does not exist: {source_output_dir}")

    actual = {
        path.relative_to(source_output_dir).as_posix()
        for path in source_output_dir.rglob("*")
        if path.is_file()
    }
    expected = set(run_record.required_artifacts)
    missing = sorted(expected - actual)
    if missing:
        raise ValueError(f"reference output is missing required artifacts: {', '.join(missing)}")
    unexpected_semantic = sorted(
        name for name in actual - expected if is_semantic_or_motion_artifact(name)
    )
    if unexpected_semantic:
        raise ValueError(f"reference output has undeclared semantic or motion artifacts: {', '.join(unexpected_semantic)}")

    destination_dir.mkdir(parents=True, exist_ok=True)
    staging = destination_dir / f".staging-{uuid.uuid4().hex}"
    current = destination_dir / "current"
    backup = destination_dir / f".previous-{uuid.uuid4().hex}"
    staging.mkdir()
    try:
        artifacts: dict[str, dict[str, object]] = {}
        for filename in run_record.required_artifacts:
            source = source_output_dir / filename
            target = staging / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            artifacts[filename] = {"sha256": _sha256(target), "size_bytes": target.stat().st_size}
        if run_record.artifact_hashes:
            observed_hashes = {filename: item["sha256"] for filename, item in artifacts.items()}
            if observed_hashes != run_record.artifact_hashes:
                raise ValueError("run record artifact hashes do not match the source output")
        manifest = {"schema_version": "ontology-watch-artifact-envelope/v1", "run": run_record.to_dict(), "artifacts": artifacts}
        (staging / "run-record.json").write_text(json.dumps(run_record.to_dict(), indent=2) + "\n", encoding="utf-8")
        (staging / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if current.exists():
            os.replace(current, backup)
        os.replace(staging, current)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists() and not current.exists():
            os.replace(backup, current)
        raise
    return current
