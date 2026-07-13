from __future__ import annotations

import json
from pathlib import Path

import pytest

from ontology_watch_generator.core.run_record import RunRecord
from ontology_watch_generator.integrations.text_to_cad.publisher import publish_reference_run


ARTIFACTS = (
    "watch.step",
    "watch.semantic.json",
    "watch.role_contracts.json",
    "watch.kinematic.json",
    "watch.validation.json",
    "watch.motion.json",
    ".watch.step.js",
    ".watch.step/model.glb",
)


def _record(*, requested_seed: int = 731, resolved_seed: int = 731) -> RunRecord:
    return RunRecord(
        pattern_id="pattern-01",
        requested_seed=requested_seed,
        resolved_seed=resolved_seed,
        source_commit="5be78528",
        backend_entrypoint="reference.entrypoint",
        design_id="seed-731",
        required_artifacts=ARTIFACTS,
    )


def _source_output(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    for name in ARTIFACTS:
        artifact = source / name
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(name, encoding="utf-8")
    return source


def test_publish_reference_run_atomically_writes_manifest(tmp_path: Path) -> None:
    current = publish_reference_run(_record(), _source_output(tmp_path), tmp_path / "published")

    manifest = json.loads((current / "MANIFEST.json").read_text(encoding="utf-8"))
    assert current.name == "current"
    assert set(manifest["artifacts"]) == set(ARTIFACTS)
    assert manifest["run"]["requested_seed"] == 731
    assert not list(current.parent.glob(".staging-*"))


@pytest.mark.parametrize("missing", ["watch.motion.json", "watch.role_contracts.json", ".watch.step.js", ".watch.step/model.glb"])
def test_publish_rejects_missing_required_artifact(tmp_path: Path, missing: str) -> None:
    source = _source_output(tmp_path)
    (source / missing).unlink()
    with pytest.raises(ValueError, match="missing required artifacts"):
        publish_reference_run(_record(), source, tmp_path / "published")


def test_publish_rejects_undeclared_semantic_artifact(tmp_path: Path) -> None:
    source = _source_output(tmp_path)
    (source / "stale.motion.json").write_text("stale", encoding="utf-8")
    with pytest.raises(ValueError, match="undeclared semantic or motion"):
        publish_reference_run(_record(), source, tmp_path / "published")


def test_publish_rejects_seed_mismatch(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requested and resolved seed"):
        publish_reference_run(_record(resolved_seed=999), _source_output(tmp_path), tmp_path / "published")
