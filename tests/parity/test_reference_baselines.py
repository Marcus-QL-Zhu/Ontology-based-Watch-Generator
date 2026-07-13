"""Contract and lightweight failure-mode tests for frozen source baselines."""

from __future__ import annotations

import glob
import gzip
import hashlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import capture_reference_baseline as capture
from scripts import reference_orchestration as orchestration


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BASELINE_DIR = REPOSITORY_ROOT / "reference_baselines"
SOURCE_COMMIT = "5be7852844a3f4c5698a737eba81c026e96ced16"
EXPECTED = {
    "pattern_01.json": ("pattern-01", 731),
    "pattern_02.json": ("pattern-02", 8459),
    "pattern_03.json": ("pattern-03", 731),
}
REQUIRED_EVIDENCE = {"solver", "semantic", "role_contracts", "motion", "kinematic", "validation"}
SPEC9_COVERAGE = {
    "occurrences",
    "roles",
    "materials_and_transparency",
    "axes_gears_bridges_and_screws",
    "motion_target_axis_ratio_direction",
    "validation_checks_reasons_and_status",
}


def _import_build123d():
    from fontTools.ttLib import TTCollection, TTFont, TTLibError

    original_glob = glob.glob

    def safe_font_glob(pattern: object, *args: object, **kwargs: object) -> list[str]:
        values = original_glob(pattern, *args, **kwargs)
        if not str(pattern).lower().endswith(("ttf", "otf", "ttc")):
            return values
        valid = []
        for value in values:
            try:
                font = TTCollection(value) if Path(value).suffix.lower() == ".ttc" else TTFont(value)
                close = getattr(font, "close", None)
                if close:
                    close()
                valid.append(value)
            except (OSError, TTLibError):
                pass
        return valid

    glob.glob = safe_font_glob
    try:
        import build123d as bd
    finally:
        glob.glob = original_glob
    return bd


def _record(filename: str) -> dict[str, object]:
    return json.loads((BASELINE_DIR / filename).read_text(encoding="utf-8"))


def _read_evidence_payload(item: dict[str, object]) -> dict[str, object]:
    path = REPOSITORY_ROOT / str(item["project_relative_path"])
    raw = gzip.decompress(path.read_bytes()) if item.get("encoding") == "gzip" else path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item["uncompressed_sha256"]
    assert len(raw) == item["uncompressed_size_bytes"]
    return json.loads(raw.decode("utf-8"))


def _source_fingerprint(
    *,
    stage_name: str = "source-stage",
    requested_seed: int = 731,
    resolved_seed: int = 731,
    candidate_id: str = "candidate-a",
    x_mm: float = 0.0,
) -> dict[str, object]:
    return orchestration.make_source_stage_fingerprint(
        stage_name=stage_name,
        requested_seed=requested_seed,
        resolved_seed=resolved_seed,
        pattern_id="pattern-01",
        source_pattern_id="central_hour_minute_offcenter_seconds",
        candidate_id=candidate_id,
        axes=[{"axis_id": "axis-a", "x_mm": x_mm, "y_mm": 0.0}],
        gears=[{"gear_id": "gear-a", "axis_id": "axis-a", "teeth": 20, "module_mm": 0.2}],
        bridge_layout_id=None,
        bridge_layout_reason="base stage does not create bridges",
        output_step_name="base.step",
    )


@pytest.mark.parametrize(("filename", "pattern_id", "seed"), [
    (filename, pattern_id, seed) for filename, (pattern_id, seed) in EXPECTED.items()
])
def test_committed_baseline_is_compact_auditable_and_path_clean(
    filename: str,
    pattern_id: str,
    seed: int,
) -> None:
    path = BASELINE_DIR / filename
    record = _record(filename)

    assert path.stat().st_size < 1_000_000
    assert record["schema_version"] == "watch-generator-reference-baseline/v4"
    assert record["pattern_id"] == pattern_id
    assert record["requested_seed"] == record["resolved_seed"] == seed
    if pattern_id == "pattern-02":
        assert record["final_step"]["sha256"]
        assert record["final_step"]["filename"].endswith((".step", ".stp"))
        assert record["final_step"]["occurrence_inventory_status"] == "pass"
        assert record["final_step"]["expected_occurrence_count"] == sum(
            orchestration.FINAL_OCCURRENCE_COUNT_INVENTORIES[pattern_id].values()
        )
        assert record["final_step"]["expected_label_count"] == len(
            orchestration.FINAL_OCCURRENCE_COUNT_INVENTORIES[pattern_id]
        )
        assert record["final_step"]["expected_occurrence_counts"] == (
            orchestration.FINAL_OCCURRENCE_COUNT_INVENTORIES[pattern_id]
        )
        assert {item["label"] for item in record["step_occurrences"]} == set(
            orchestration.FINAL_OCCURRENCE_INVENTORIES[pattern_id]
        )
        assert record["final_external_envelope"]["violations"] == []
        assert tuple(record["final_external_envelope"]["expected_external_occurrences"]) == (
            orchestration.FINAL_EXTERNAL_OCCURRENCE_INVENTORIES[pattern_id]
        )
        assert record["runtime_provenance"]["materialized_external_step_sha256"] == (
            "313e49a2c323b84d68c2aa47df92ef0c1368338601df83cc9e320cde751c4eae"
        )
        final_artifact = next(
            item for item in record["artifacts"]
            if item["filename"] == record["final_step"]["filename"]
        )
        assert final_artifact["sha256"] == record["final_step"]["sha256"]
        for stage in record["stages"]:
            fingerprint = stage["stage_fingerprint"]
            if fingerprint["observation_kind"] == "artifact_lineage":
                assert fingerprint["input_artifact"] == record["final_step"]["filename"]
                assert fingerprint["input_sha256"] == record["final_step"]["sha256"]
    assert record["source"]["commit"] == SOURCE_COMMIT
    assert record["source"]["worktree_unchanged"] is True
    assert record["source"]["execution_boundary"] == "git archive snapshot only"
    assert "C:\\Users\\" not in path.read_text(encoding="utf-8")

    stages = record["stages"]
    assert [stage["name"] for stage in stages] == [
        stage.name for stage in orchestration.PATTERNS[pattern_id].stages
    ]
    assert all(stage["status"] == "pass" for stage in stages)
    assert all(stage["policy"] == "required_pass" for stage in stages)
    assert all("result" not in stage and "outputs" not in stage for stage in stages)
    assert all("stage_fingerprint" in stage for stage in stages)

    assert record["step_occurrences"]
    assert len({item["label"] for item in record["step_occurrences"]}) == len(record["step_occurrences"])
    assert set(record["spec9_coverage"]) == SPEC9_COVERAGE
    assert all(record["spec9_coverage"][key] for key in SPEC9_COVERAGE)

    for item in record["source_evidence"].values():
        if item["status"] != "captured":
            assert item["value"] is None and item["reason"]
            continue
        evidence_path = REPOSITORY_ROOT / item["project_relative_path"]
        assert evidence_path.is_file()
        assert evidence_path.resolve().is_relative_to((BASELINE_DIR / "source_evidence").resolve())
        assert hashlib.sha256(evidence_path.read_bytes()).hexdigest() == item["sha256"]
        raw = gzip.decompress(evidence_path.read_bytes()) if item.get("encoding") == "gzip" else evidence_path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["uncompressed_sha256"]
        assert len(raw) == item["uncompressed_size_bytes"]
        assert "C:\\Users\\" not in raw.decode("utf-8")

    required_payload_fields = {
        "solver": {"status", "seed", "selected_candidate"},
        "semantic": {"status", "seed", "checks"},
        "role_contracts": {"status", "roles", "contracts"},
        "motion": {"status", "moving_groups", "fixed_features", "semantic_material_contracts", "visual_materials"},
        "kinematic": {"status", "checks"},
        "validation": {"status", "failed_checks", "checks"},
    }
    for kind, required_fields in required_payload_fields.items():
        item = record["source_evidence"][kind]
        if item["status"] != "captured":
            continue
        payload = _read_evidence_payload(item)
        assert required_fields <= set(payload)
        assert payload["status"] == "pass"
        if kind == "validation":
            assert payload["failed_checks"] == []

    postprocessed = {
        artifact["filename"]: artifact
        for artifact in record["artifacts"]
        if artifact.get("derivation") == "postprocessed_by_browser_sync"
    }
    assert any(name.endswith(".motion.json") for name in postprocessed)
    assert any(name.endswith(".step.js") for name in postprocessed)

    assert record["status"] == "pass"
    assert all(record["source_evidence"][kind]["status"] == "captured" for kind in REQUIRED_EVIDENCE)
    if pattern_id == "pattern-03":
        for kind in ("solver", "semantic", "role_contracts", "kinematic"):
            provenance = record["source_evidence"][kind]["provenance"]
            assert provenance["complete_entrypoint_pattern_card_id"] == (
                "pattern4_independent_hour_minute_no_seconds_v1"
            )
            assert provenance["generation_seed"] == 731


def test_fingerprint_gate_rejects_silent_seed_substitution() -> None:
    first = _source_fingerprint(requested_seed=731, resolved_seed=999)
    second = _source_fingerprint(stage_name="second", requested_seed=731, resolved_seed=999)

    with pytest.raises(ValueError, match="requested seed 731 resolved as 999"):
        orchestration.assert_matching_fingerprints([first, second], requested_seed=731)


def test_fingerprint_gate_rejects_missing_observation() -> None:
    fingerprint = _source_fingerprint()
    del fingerprint["candidate_id"]

    with pytest.raises(ValueError, match="missing observed fields"):
        orchestration.assert_matching_fingerprints([fingerprint], requested_seed=731)


def test_fingerprint_gate_rejects_candidate_and_geometry_drift() -> None:
    expected = _source_fingerprint()

    with pytest.raises(ValueError, match="candidate_id"):
        orchestration.assert_matching_fingerprints(
            [expected, _source_fingerprint(stage_name="second", candidate_id="candidate-b")],
            requested_seed=731,
        )
    with pytest.raises(ValueError, match="design_digest"):
        orchestration.assert_matching_fingerprints(
            [expected, _source_fingerprint(stage_name="second", x_mm=1.0)],
            requested_seed=731,
        )


def test_unavailable_stage_observations_are_explicit_null_with_reason() -> None:
    fingerprint = orchestration.make_derived_stage_fingerprint(
        stage_name="step_to_glb",
        requested_seed=731,
        input_artifact="final.step",
        input_sha256="a" * 64,
        output_artifact=".final.step.glb",
        output_sha256="b" * 64,
    )

    for field in ("resolved_seed", "candidate_id", "axes", "gears", "design_digest", "bridge_layout_id"):
        assert fingerprint[field] is None
        assert fingerprint["unavailable_reasons"][field]


def _fake_result(pattern_id: str, seed: int) -> dict[str, object]:
    stages = []
    for stage in orchestration.PATTERNS[pattern_id].stages:
        if stage.classification == orchestration.SOURCE_NATIVE:
            fingerprint = _source_fingerprint(stage_name=stage.name, requested_seed=seed, resolved_seed=seed)
        else:
            fingerprint = orchestration.make_derived_stage_fingerprint(
                stage_name=stage.name,
                requested_seed=seed,
                input_artifact="final.step",
                input_sha256="a" * 64,
                output_artifact="derived.bin",
                output_sha256="b" * 64,
            )
        stages.append({"name": stage.name, "status": "pass", "stage_fingerprint": fingerprint})
    return {"stages": stages, "final_step": "final.step", "glb": ".final.step.glb"}


@pytest.mark.parametrize(("stage_name", "message"), [
    ("base_engineering_evidence", "required source-native stage failed"),
    ("step_to_glb", "required derived stage failed"),
    ("browser_sync", "required derived stage failed"),
])
def test_required_stage_failures_are_never_promoted(stage_name: str, message: str) -> None:
    result = _fake_result("pattern-02", 8459)
    next(stage for stage in result["stages"] if stage["name"] == stage_name)["status"] = "fail"

    with pytest.raises(ValueError, match=message):
        orchestration.validate_orchestration_result(
            orchestration.PATTERNS["pattern-02"], result, requested_seed=8459
        )


def test_partial_native_failure_reports_the_stage_before_missing_derived_work() -> None:
    result = _fake_result("pattern-02", 8459)
    result["stages"] = result["stages"][:3]
    result["stages"][0]["status"] = "fail"

    with pytest.raises(ValueError, match="required source-native stage failed: base_engineering_evidence"):
        orchestration.validate_orchestration_result(
            orchestration.PATTERNS["pattern-02"], result, requested_seed=8459
        )


def test_artifact_classification_marks_post_sync_motion_and_js_as_derived() -> None:
    postprocessed = {
        "watch.motion.json": "browser_sync",
        ".watch.step.js": "browser_sync",
    }

    assert capture.classify_artifact("watch.validation.json", postprocessed)["classification"] == "source_native"
    assert capture.classify_artifact(".watch.step.glb", postprocessed)["classification"] == "derived"
    for filename in postprocessed:
        classification = capture.classify_artifact(filename, postprocessed)
        assert classification == {"classification": "derived", "derivation": "postprocessed_by_browser_sync"}


def test_report_evidence_requires_an_exact_top_level_schema(tmp_path: Path) -> None:
    report = tmp_path / "complete_report.json"
    report.write_text(json.dumps({"summary": {"semantic": {"status": "pass", "seed": 731}}}), encoding="utf-8")

    evidence = capture.discover_native_evidence(tmp_path, "pattern-03")

    assert evidence["semantic"]["status"] == "absent"
    assert evidence["semantic"]["value"] is None
    assert "exact source schema" in evidence["semantic"]["reason"]


def test_pattern3_complete_report_captures_embedded_raw_evidence_losslessly(tmp_path: Path) -> None:
    payloads = {
        "solver": {
            "kind": "watch_independent_display_solver_report", "status": "pass", "seed": 731,
            "selected_candidate": {"candidate_id": "seed-731"},
        },
        "semantic": {
            "kind": "watch_power_chain_mvp_semantic_report", "status": "pass", "seed": 731,
            "checks": {"semantic": "pass"},
        },
        "role_contracts": {
            "kind": "watch_power_chain_mvp_role_contract_report", "status": "pass",
            "roles": ["driver"], "contracts": [{"occurrence_id": "axis"}],
        },
        "kinematic": {
            "kind": "watch_power_chain_mvp_kinematic_report", "status": "pass",
            "checks": {"ratio": "pass"},
        },
    }
    sources = {
        name: {
            "complete_entrypoint_pattern_card_id": "pattern4_independent_hour_minute_no_seconds_v1",
            "generation_seed": 731,
            "builder": f"build_{name}",
            "payload_pattern_card_id": "independent_hour_minute_no_seconds_v1",
        }
        for name in payloads
    }
    report = {
        "kind": "watch_pattern4_independent_display_complete_model_generation",
        "pattern_card_id": "pattern4_independent_hour_minute_no_seconds_v1",
        "status": "pass",
        "seed": 731,
        "validation": {"status": "pass", "failed_checks": [], "checks": {}},
        "evidence": {
            name: {"source": sources[name], "payload": payload}
            for name, payload in payloads.items()
        },
    }
    (tmp_path / "pattern4_independent_display_complete_model_report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    evidence = capture.discover_native_evidence(tmp_path, "pattern-03")

    for name, payload in payloads.items():
        assert evidence[name]["status"] == "captured"
        assert evidence[name]["preservation"] == "lossless_json_subtree_extract"
        assert evidence[name]["json_pointer"] == f"/evidence/{name}/payload"
        assert evidence[name]["provenance"] == sources[name]
        assert evidence[name]["_payload"] == payload

    capture.validate_pattern3_complete_evidence_identity(
        evidence,
        requested_seed=731,
        complete_entrypoint_pattern_card_id="pattern4_independent_hour_minute_no_seconds_v1",
    )
    evidence["kinematic"]["provenance"]["generation_seed"] = 999
    with pytest.raises(capture.CaptureFailure, match="generation seed differs"):
        capture.validate_pattern3_complete_evidence_identity(
            evidence,
            requested_seed=731,
            complete_entrypoint_pattern_card_id="pattern4_independent_hour_minute_no_seconds_v1",
        )


def test_large_native_evidence_is_gzip_archived_losslessly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(capture, "SOURCE_EVIDENCE_DIRECTORY", tmp_path)
    monkeypatch.setattr(capture, "REPOSITORY_ROOT", tmp_path.parent)
    payload = {
        "status": "pass",
        "seed": 731,
        "selected_candidate": "candidate-a",
        "candidate_trace": "x" * (capture.COMPRESSED_EVIDENCE_THRESHOLD_BYTES + 1),
    }
    archived = capture.archive_native_evidence(
        "pattern-test",
        {
            "solver": {
                "status": "captured",
                "preservation": "lossless_json_subtree_extract",
                "_payload": payload,
            }
        },
    )["solver"]

    path = tmp_path / "pattern-test" / "solver.json.gz"
    assert archived["encoding"] == "gzip"
    assert path.is_file()
    raw = gzip.decompress(path.read_bytes())
    assert json.loads(raw.decode("utf-8")) == payload
    assert archived["uncompressed_sha256"] == hashlib.sha256(raw).hexdigest()


def test_missing_or_malformed_native_evidence_blocks_capture(tmp_path: Path) -> None:
    (tmp_path / "watch.solver.json").write_text('{"status": "pass"}', encoding="utf-8")

    evidence = capture.discover_native_evidence(tmp_path, "pattern-01")
    missing = capture.missing_required_evidence(evidence)

    assert "solver" in missing
    assert set(missing) >= REQUIRED_EVIDENCE


def test_generation_output_must_be_new_and_under_system_temp(tmp_path: Path) -> None:
    outside = REPOSITORY_ROOT / "not-a-temp-output"
    with pytest.raises(ValueError, match="system temporary"):
        capture.ensure_new_system_temporary_directory(outside)

    fresh = Path(tempfile.gettempdir()) / "ontology-watch-policy-test-new"
    if fresh.exists():
        fresh.rmdir()
    assert capture.ensure_new_system_temporary_directory(fresh) == fresh.resolve()
    with pytest.raises(ValueError, match="newly created and empty"):
        capture.ensure_new_system_temporary_directory(fresh)
    fresh.rmdir()


def test_snapshot_and_generation_directories_must_be_disjoint(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    output = snapshot / "output"
    snapshot.mkdir()

    with pytest.raises(ValueError, match="outside the archive snapshot"):
        orchestration.validate_execution_paths(snapshot, output)


def test_reference_python_defaults_to_source_venv(tmp_path: Path) -> None:
    source = tmp_path / "source"
    reference_python = source / ".venv" / "Scripts" / "python.exe"
    reference_python.parent.mkdir(parents=True)
    reference_python.touch()

    assert capture.resolve_reference_python(source) == reference_python.resolve()


def test_reference_python_requires_default_source_venv(tmp_path: Path) -> None:
    with pytest.raises(orchestration.CaptureFailure, match="runtime root .venv"):
        capture.resolve_reference_python(tmp_path)


def test_reference_python_can_use_explicit_runtime_root(tmp_path: Path) -> None:
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    reference_python = runtime / ".venv" / "Scripts" / "python.exe"
    source.mkdir()
    reference_python.parent.mkdir(parents=True)
    reference_python.touch()

    assert capture.resolve_reference_python(source, runtime) == reference_python.resolve()


def test_explicit_runtime_root_never_falls_back_to_source_or_host_python(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source_python = source / ".venv" / "Scripts" / "python.exe"
    source_python.parent.mkdir(parents=True)
    source_python.touch()
    missing_runtime = tmp_path / "missing-runtime"

    with pytest.raises(orchestration.CaptureFailure, match="runtime root .venv") as failure:
        capture.resolve_reference_python(source, missing_runtime)

    assert failure.value.details["runtime_root"] == str(missing_runtime.resolve())
    assert failure.value.details["expected_interpreter"] == ".venv/Scripts/python.exe"


def test_parse_args_accepts_explicit_runtime_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(
        capture.sys,
        "argv",
        [
            "capture_reference_baseline.py",
            "--pattern", "pattern-01",
            "--seed", "731",
            "--output", str(tmp_path / "output"),
            "--source", str(tmp_path / "source"),
            "--runtime-root", str(runtime),
            "--viewer-dir", str(tmp_path / "viewer"),
        ],
    )

    assert capture.parse_args().runtime_root == runtime


def test_materialized_external_step_accepts_archive_smudge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    snapshot = tmp_path / "snapshot"
    source_step = source / capture.EXTERNAL_STEP_RELATIVE_PATH
    snapshot_step = snapshot / capture.EXTERNAL_STEP_RELATIVE_PATH
    source_step.parent.mkdir(parents=True)
    snapshot_step.parent.mkdir(parents=True)
    source_step.write_bytes(b"materialized-step")
    snapshot_step.write_bytes(source_step.read_bytes())
    pointer_oid = hashlib.sha256(source_step.read_bytes()).hexdigest()
    monkeypatch.setattr(
        capture,
        "run_git",
        lambda *_args: f"version https://git-lfs.github.com/spec/v1\noid sha256:{pointer_oid}\nsize 17",
    )

    assert capture.materialize_external_step(source, snapshot) == snapshot_step


def test_materialized_external_step_rejects_equal_smudged_bytes_not_matching_frozen_lfs_oid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    snapshot = tmp_path / "snapshot"
    source_step = source / capture.EXTERNAL_STEP_RELATIVE_PATH
    snapshot_step = snapshot / capture.EXTERNAL_STEP_RELATIVE_PATH
    source_step.parent.mkdir(parents=True)
    snapshot_step.parent.mkdir(parents=True)
    source_step.write_bytes(b"not-the-frozen-lfs-object")
    snapshot_step.write_bytes(source_step.read_bytes())
    monkeypatch.setattr(
        capture,
        "run_git",
        lambda *_args: (
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:313e49a2c323b84d68c2aa47df92ef0c1368338601df83cc9e320cde751c4eae\n"
            "size 1190969"
        ),
    )

    with pytest.raises(capture.CaptureFailure, match="frozen LFS pointer"):
        capture.materialize_external_step(source, snapshot)


def test_runtime_provenance_is_relative_and_hashes_materialized_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    external_step = tmp_path / capture.EXTERNAL_STEP_RELATIVE_PATH
    external_step.parent.mkdir(parents=True)
    external_step.write_bytes(b"materialized-step")
    monkeypatch.setattr(
        capture.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "python_executable": str((tmp_path / ".venv" / "Scripts" / "python.exe").resolve()),
                "python_version": "3.11.9",
                "build123d_version": "0.10.0",
            }) + "\n",
            stderr="",
        ),
    )

    provenance = capture.capture_runtime_provenance(
        tmp_path / ".venv" / "Scripts" / "python.exe",
        tmp_path,
        external_step,
    )

    assert provenance == {
        "source_code_root": "frozen_git_archive_snapshot",
        "runtime_root": "source_worktree_default",
        "python_executable": ".venv/Scripts/python.exe",
        "python_version": "3.11.9",
        "build123d_version": "0.10.0",
        "materialized_external_step_path": capture.EXTERNAL_STEP_RELATIVE_PATH.as_posix(),
        "materialized_external_step_sha256": hashlib.sha256(b"materialized-step").hexdigest(),
    }


def test_runtime_provenance_records_explicit_runtime_root_without_absolute_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    runtime = tmp_path / "runtime"
    reference_python = runtime / ".venv" / "Scripts" / "python.exe"
    external_step = snapshot / capture.EXTERNAL_STEP_RELATIVE_PATH
    external_step.parent.mkdir(parents=True)
    external_step.write_bytes(b"materialized-step")
    monkeypatch.setattr(
        capture.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "python_executable": str(reference_python.resolve()),
                "python_version": "3.11.9",
                "build123d_version": "0.10.0",
            }) + "\n",
            stderr="",
        ),
    )

    provenance = capture.capture_runtime_provenance(
        reference_python,
        snapshot,
        external_step,
        runtime_root_kind="explicit_runtime_root",
    )

    assert provenance["source_code_root"] == "frozen_git_archive_snapshot"
    assert provenance["runtime_root"] == "explicit_runtime_root"
    assert str(runtime.resolve()) not in json.dumps(provenance)


def test_runtime_provenance_rejects_wrong_interpreter_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    external_step = tmp_path / capture.EXTERNAL_STEP_RELATIVE_PATH
    external_step.parent.mkdir(parents=True)
    external_step.write_bytes(b"materialized-step")
    monkeypatch.setattr(
        capture.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "python_executable": str((tmp_path / "host-python.exe").resolve()),
                "python_version": "3.11.9",
                "build123d_version": "0.10.0",
            }) + "\n",
            stderr="",
        ),
    )

    with pytest.raises(capture.CaptureFailure, match="interpreter provenance"):
        capture.capture_runtime_provenance(
            tmp_path / ".venv" / "Scripts" / "python.exe",
            tmp_path,
            external_step,
        )


def test_runtime_provenance_rejects_untrusted_build123d_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference_python = tmp_path / ".venv" / "Scripts" / "python.exe"
    external_step = tmp_path / capture.EXTERNAL_STEP_RELATIVE_PATH
    external_step.parent.mkdir(parents=True)
    external_step.write_bytes(b"materialized-step")
    monkeypatch.setattr(
        capture.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "python_executable": str(reference_python.resolve()),
                "python_version": "3.11.9",
                "build123d_version": "0.11.0",
            }) + "\n",
            stderr="",
        ),
    )

    with pytest.raises(capture.CaptureFailure, match="build123d version"):
        capture.capture_runtime_provenance(reference_python, tmp_path, external_step)


def test_detached_external_leaf_blocks_final_step(tmp_path: Path) -> None:
    bd = _import_build123d()

    wheel = bd.Box(1.0, 1.0, 1.0)
    wheel.label = "external_escape_wheel"
    staff = bd.Box(1.0, 1.0, 1.0).translate((30.0, 0.0, 0.0))
    staff.label = "external_escape_staff"
    fixture = bd.Compound(children=[wheel, staff])
    fixture.label = "detached_external_fixture"
    detached_external_fixture_step = tmp_path / "detached_external.step"
    bd.export_step(fixture, detached_external_fixture_step)

    violations = orchestration.validate_final_escapement_envelope(
        detached_external_fixture_step,
        {"x": [-22.0, 22.0], "y": [-22.0, 22.0], "z": [-0.675, 5.16]},
        expected_external_occurrences=("external_escape_wheel", "external_escape_staff"),
    )

    assert {item["occurrence"] for item in violations} == {"external_escape_staff"}


@pytest.mark.parametrize(
    ("labels", "expected_kinds"),
    [
        (("external_escape_wheel",), {"missing_external_occurrence"}),
        (
            ("external_escape_wheel", "external_escape_staff", "external_decoy"),
            {"unexpected_external_occurrence"},
        ),
        (
            ("external_escape_wheel", "external_escape_staff", "external_escape_staff"),
            {"duplicate_external_occurrence"},
        ),
    ],
)
def test_external_inventory_is_exact(
    tmp_path: Path,
    labels: tuple[str, ...],
    expected_kinds: set[str],
) -> None:
    bd = _import_build123d()

    leaves = []
    for index, label in enumerate(labels):
        leaf = bd.Box(0.5, 0.5, 0.5).translate((index, 0, 0))
        leaf.label = label
        leaves.append(leaf)
    fixture = bd.Compound(children=leaves)
    step = tmp_path / "inventory.step"
    bd.export_step(fixture, step)

    violations = orchestration.validate_final_escapement_envelope(
        step,
        {"x": [-22.0, 22.0], "y": [-22.0, 22.0], "z": [-1.0, 5.16]},
        expected_external_occurrences=("external_escape_wheel", "external_escape_staff"),
    )

    assert expected_kinds <= {item["kind"] for item in violations}


def test_renamed_remote_leaf_and_in_envelope_external_decoy_cannot_bypass_gate(tmp_path: Path) -> None:
    bd = _import_build123d()

    wheel = bd.Box(1, 1, 1)
    wheel.label = "external_escape_wheel"
    renamed_staff = bd.Box(1, 1, 1).translate((30, 0, 0))
    renamed_staff.label = "escape_staff_geometry"
    decoy = bd.Box(1, 1, 1).translate((1, 0, 0))
    decoy.label = "external_escape_staff"
    fixture = bd.Compound(children=[wheel, renamed_staff, decoy])
    step = tmp_path / "renamed-decoy.step"
    bd.export_step(fixture, step)

    violations = orchestration.validate_final_escapement_envelope(
        step,
        {"x": [-22.0, 22.0], "y": [-22.0, 22.0], "z": [-1.0, 5.16]},
        expected_external_occurrences=("external_escape_wheel", "external_escape_staff"),
        expected_final_occurrences=("COMPOUND", "external_escape_wheel", "external_escape_staff"),
    )

    assert {item["kind"] for item in violations} >= {
        "unexpected_final_occurrence",
        "leaf_outside_final_envelope",
    }
    assert any(item.get("occurrence") == "escape_staff_geometry" for item in violations)


def test_duplicate_expected_final_label_cannot_hide_detached_geometry(tmp_path: Path) -> None:
    bd = _import_build123d()

    decoy = bd.Box(1, 1, 1)
    decoy.label = "external_escape_staff"
    foundation = bd.Box(1, 1, 1).translate((1, 0, 0))
    foundation.label = "foundation_mainplate"
    detached = bd.Box(1, 1, 1).translate((30, 0, 0))
    detached.label = "foundation_mainplate"
    fixture = bd.Compound(children=[decoy, foundation, detached])
    step = tmp_path / "duplicate-final-label.step"
    bd.export_step(fixture, step)

    violations = orchestration.validate_final_escapement_envelope(
        step,
        {"x": [-22.0, 22.0], "y": [-22.0, 22.0], "z": [-1.0, 5.16]},
        expected_external_occurrences=("external_escape_staff",),
        expected_final_occurrences=("COMPOUND", "external_escape_staff", "foundation_mainplate"),
    )

    assert any(
        item["kind"] == "duplicate_final_occurrence"
        and item["occurrence"] == "foundation_mainplate"
        and item["expected_count"] == 1
        and item["observed_count"] == 2
        for item in violations
    )


def test_final_step_identity_binds_source_output_and_derived_hashes(tmp_path: Path) -> None:
    final_step = tmp_path / "final.step"
    final_step.write_bytes(b"final-step")
    result = _fake_result("pattern-02", 8459)
    result["final_step"] = str(final_step)
    source_stage = next(
        stage for stage in reversed(result["stages"])
        if stage["stage_fingerprint"]["observation_kind"] == "source_design"
    )
    source_stage["stage_fingerprint"]["output_step_name"] = final_step.name
    source_stage["stage_fingerprint"]["output_step_path"] = str(final_step.resolve())
    source_stage["stage_fingerprint"]["unavailable_reasons"].pop("output_step_name", None)
    expected_hash = hashlib.sha256(final_step.read_bytes()).hexdigest()
    source_stage["stage_fingerprint"]["output_step_sha256"] = expected_hash
    for stage in result["stages"]:
        fingerprint = stage["stage_fingerprint"]
        if fingerprint["observation_kind"] == "artifact_lineage":
            fingerprint["input_artifact"] = final_step.name
            fingerprint["input_artifact_path"] = str(final_step.resolve())
            fingerprint["input_sha256"] = expected_hash

    assert orchestration.validate_final_step_identity(result, tmp_path) == expected_hash

    result["stages"][-1]["stage_fingerprint"]["input_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="final STEP hash"):
        orchestration.validate_final_step_identity(result, tmp_path)

    result["stages"][-1]["stage_fingerprint"]["input_sha256"] = expected_hash
    decoy_step = tmp_path / "decoy.step"
    decoy_step.write_bytes(b"final-step")
    result["final_step"] = str(decoy_step)
    with pytest.raises(ValueError, match="final source-stage STEP"):
        orchestration.validate_final_step_identity(result, tmp_path)


def test_final_step_identity_rejects_same_basename_in_different_run_subdirectory(
    tmp_path: Path,
) -> None:
    source_step = tmp_path / "source-stage" / "final.step"
    source_step.parent.mkdir()
    source_step.write_bytes(b"source-stage-step")
    decoy_step = tmp_path / "decoy" / "final.step"
    decoy_step.parent.mkdir()
    decoy_step.write_bytes(b"decoy-step")
    decoy_hash = hashlib.sha256(decoy_step.read_bytes()).hexdigest()

    result = _fake_result("pattern-02", 8459)
    result["final_step"] = str(decoy_step.resolve())
    source_stage = next(
        stage for stage in reversed(result["stages"])
        if stage["stage_fingerprint"]["observation_kind"] == "source_design"
    )
    source_stage["stage_fingerprint"].update({
        "output_step_name": source_step.name,
        "output_step_path": str(source_step.resolve()),
        "output_step_sha256": hashlib.sha256(source_step.read_bytes()).hexdigest(),
    })
    for stage in result["stages"]:
        fingerprint = stage["stage_fingerprint"]
        if fingerprint["observation_kind"] == "artifact_lineage":
            fingerprint["input_artifact"] = decoy_step.name
            fingerprint["input_sha256"] = decoy_hash

    with pytest.raises(ValueError, match="final source-stage STEP"):
        orchestration.validate_final_step_identity(result, tmp_path)


def _captured_evidence(payload: dict[str, object]) -> dict[str, object]:
    return {"status": "captured", "_payload": payload}


@pytest.mark.parametrize(
    ("kind", "payload", "message"),
    [
        ("solver", {"seed": 999, "pattern_card_id": "separate_hour_minute_no_seconds_v1"}, "seed"),
        ("semantic", {"seed": 8459, "pattern_card_id": "wrong-pattern"}, "pattern_card_id"),
        ("complete_geometry_report", {"seed": 999, "pattern_card_id": "wrong-pattern"}, "seed"),
        ("bridge_checklist", {"seed": 999, "pattern_card_id": "wrong-pattern"}, "seed"),
    ],
)
def test_evidence_report_and_checklist_identity_must_match_run(
    kind: str,
    payload: dict[str, object],
    message: str,
) -> None:
    evidence = {kind: _captured_evidence(payload)}

    with pytest.raises(capture.CaptureFailure, match=message):
        capture.validate_evidence_identity(
            evidence,
            requested_seed=8459,
            source_pattern_id="separate_hour_minute_no_seconds_v1",
        )


def test_conflicting_matching_native_sidecars_fail_discovery(tmp_path: Path) -> None:
    expected = {
        "kind": "semantic_validation",
        "status": "pass",
        "seed": 8459,
        "pattern_card_id": "separate_hour_minute_no_seconds_v1",
        "checks": [],
    }
    conflicting = {
        **expected,
        "seed": 999,
        "pattern_card_id": "wrong-pattern",
    }
    (tmp_path / "a.semantic.json").write_text(json.dumps(expected), encoding="utf-8")
    (tmp_path / "z.semantic.json").write_text(json.dumps(conflicting), encoding="utf-8")

    with pytest.raises(capture.CaptureFailure, match="conflicting native evidence sidecars"):
        capture.discover_native_evidence(tmp_path, "pattern-02")


def test_final_step_named_sidecar_cannot_hide_conflicting_identity(tmp_path: Path) -> None:
    expected = {
        "kind": "semantic_validation",
        "status": "pass",
        "seed": 8459,
        "pattern_card_id": "separate_hour_minute_no_seconds_v1",
        "checks": [],
    }
    conflicting = {
        **expected,
        "seed": 999,
        "pattern_card_id": "wrong-pattern",
    }
    (tmp_path / "final.semantic.json").write_text(json.dumps(expected), encoding="utf-8")
    (tmp_path / "z.semantic.json").write_text(json.dumps(conflicting), encoding="utf-8")
    final_step = tmp_path / "final.step"
    final_step.write_bytes(b"final")

    with pytest.raises(capture.CaptureFailure, match="conflicting native evidence sidecars"):
        capture.discover_native_evidence(
            tmp_path,
            "pattern-02",
            final_step=final_step,
        )


def test_native_sidecar_bound_to_final_step_is_not_confused_with_base_stage_sidecar(
    tmp_path: Path,
) -> None:
    base = {
        "kind": "motion",
        "status": "pass",
        "pattern_card_id": "separate_hour_minute_no_seconds_v1",
        "moving_groups": [],
        "fixed_features": [],
        "semantic_material_contracts": {},
        "visual_materials": {},
    }
    final = {**base, "moving_groups": [{"group_id": "final"}]}
    (tmp_path / "watch_power_chain_mvp.motion.json").write_text(
        json.dumps(base), encoding="utf-8"
    )
    (tmp_path / "final.motion.json").write_text(json.dumps(final), encoding="utf-8")
    final_step = tmp_path / "final.step"
    final_step.write_bytes(b"final")

    evidence = capture.discover_native_evidence(
        tmp_path,
        "pattern-02",
        final_step=final_step,
    )

    assert evidence["motion"]["source_filename"] == "final.motion.json"
    assert evidence["motion"]["_payload"] == final


def test_stage_fingerprint_paths_are_made_run_relative_for_the_baseline(tmp_path: Path) -> None:
    final_step = tmp_path / "source-stage" / "final.step"
    final_step.parent.mkdir()
    final_step.write_bytes(b"final-step")
    fingerprint = {
        "output_step_path": str(final_step.resolve()),
        "input_artifact_path": str(final_step.resolve()),
    }

    portable = capture.portable_stage_fingerprint(fingerprint, tmp_path)

    assert portable == {
        "output_step_path": "source-stage/final.step",
        "input_artifact_path": "source-stage/final.step",
    }
    assert fingerprint["output_step_path"] == str(final_step.resolve())


def test_formal_chain_process_runs_from_the_archive_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = tmp_path / "snapshot"
    output = tmp_path / "output"
    snapshot.mkdir()
    output.mkdir()
    result = _fake_result("pattern-01", 731)
    final_step = output / "final.step"
    final_step.write_bytes(b"final-step")
    final_hash = hashlib.sha256(final_step.read_bytes()).hexdigest()
    result["final_step"] = str(final_step)
    source_stages = [
        stage for stage in result["stages"]
        if stage["stage_fingerprint"]["observation_kind"] == "source_design"
    ]
    source_stages[-1]["stage_fingerprint"]["output_step_name"] = final_step.name
    source_stages[-1]["stage_fingerprint"]["output_step_path"] = str(final_step.resolve())
    source_stages[-1]["stage_fingerprint"]["output_step_sha256"] = final_hash
    for stage in result["stages"]:
        fingerprint = stage["stage_fingerprint"]
        if fingerprint["observation_kind"] == "artifact_lineage":
            fingerprint["input_artifact"] = final_step.name
            fingerprint["input_artifact_path"] = str(final_step.resolve())
            fingerprint["input_sha256"] = final_hash
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        observed["command"] = command
        observed.update(kwargs)
        return SimpleNamespace(
            returncode=0,
            stdout=orchestration.RESULT_MARKER + json.dumps(result) + "\n",
            stderr="",
        )

    monkeypatch.setattr(orchestration.subprocess, "run", fake_run)

    reference_python = tmp_path / "source" / ".venv" / "Scripts" / "python.exe"
    orchestration.run_formal_chain(snapshot, output, "pattern-01", 731, reference_python)

    assert Path(observed["cwd"]) == snapshot
    assert Path(observed["command"][0]) == reference_python
    assert str(snapshot) in observed["env"]["PYTHONPATH"].split(orchestration.os.pathsep)


def test_source_write_guard_detects_tracked_untracked_or_ignored_changes() -> None:
    before = {"head": SOURCE_COMMIT, "status": "", "tree_state_sha256": "a" * 64}
    after = {**before, "tree_state_sha256": "b" * 64}

    with pytest.raises(RuntimeError, match="source worktree changed"):
        capture.assert_source_unchanged(before, after)


def test_source_write_guard_runs_in_finally_after_capture_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fingerprints = iter([
        {"head": SOURCE_COMMIT, "status": "", "tree_state_sha256": "a" * 64},
        {"head": SOURCE_COMMIT, "status": "", "tree_state_sha256": "b" * 64},
    ])
    monkeypatch.setattr(capture, "source_worktree_fingerprint", lambda _root: next(fingerprints))

    with pytest.raises(RuntimeError, match="source worktree changed"):
        with capture.source_write_guard(tmp_path):
            raise capture.CaptureFailure("generation failed")


def test_review_screenshot_hashes_match_copied_files() -> None:
    for filename in EXPECTED:
        record = _record(filename)
        for screenshot in record["screenshots"]["artifacts"]:
            path = BASELINE_DIR / "screenshots" / screenshot["filename"]
            assert path.is_file()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == screenshot["sha256"]
