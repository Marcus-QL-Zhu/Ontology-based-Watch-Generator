"""Guard the frozen source import used by the reference backend."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_CHECKOUT_ENV = "ONTOLOGY_WATCH_TEXT_TO_CAD_SOURCE"
FROZEN_SOURCE_ROOT = Path(os.environ[SOURCE_CHECKOUT_ENV]).resolve() if os.environ.get(SOURCE_CHECKOUT_ENV) else None
REFERENCE_BACKEND = PROJECT_ROOT / "src" / "ontology_watch_generator" / "reference_backend"
SOURCE_MAP_PATH = REFERENCE_BACKEND / "SOURCE_MAP.json"
EXPECTED_COMMIT = "5be7852844a3f4c5698a737eba81c026e96ced16"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_relative_paths() -> set[str]:
    assert FROZEN_SOURCE_ROOT is not None
    source_root = FROZEN_SOURCE_ROOT / "models" / "watch_kinematic"
    copied_roots = (
        source_root / "watch_kinematic",
        source_root / "tests",
        source_root / "references" / "escapement",
    )
    return {
        path.relative_to(FROZEN_SOURCE_ROOT).as_posix()
        for copied_root in copied_roots
        for path in copied_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
        and (
            path.suffix == ".py"
            or path == source_root / "watch_kinematic" / "pattern_cards" / "AGENTS.md"
        )
    }


def _load_source_map() -> dict[str, object]:
    assert SOURCE_MAP_PATH.is_file(), "SOURCE_MAP.json is missing"
    return json.loads(SOURCE_MAP_PATH.read_text(encoding="utf-8"))


def test_source_map_covers_complete_frozen_orchestration_closure() -> None:
    source_map = _load_source_map()
    assert source_map["frozen_source_commit"] == EXPECTED_COMMIT
    assert source_map["source_repository"] == "https://github.com/earthtojake/text-to-cad"
    assert "C:/Users/" not in json.dumps(source_map)
    if FROZEN_SOURCE_ROOT is None:
        pytest.skip(f"set {SOURCE_CHECKOUT_ENV} to audit the original source checkout")
    mapped_sources = {entry["source"] for entry in source_map["files"]}
    assert _source_relative_paths() <= mapped_sources


def test_source_map_rejects_unmapped_copies_missing_files_and_hash_mismatches() -> None:
    source_map = _load_source_map()
    entries = source_map["files"]
    mapped_destinations = {entry["destination"] for entry in entries}
    copied_files = {
        path.relative_to(REFERENCE_BACKEND).as_posix()
        for copied_root in (
            REFERENCE_BACKEND / "watch_kinematic",
            REFERENCE_BACKEND / "tests",
            REFERENCE_BACKEND / "references",
        )
        if copied_root.is_dir()
        for path in copied_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    }
    assert copied_files == mapped_destinations

    for entry in entries:
        destination = REFERENCE_BACKEND / entry["destination"]
        assert destination.is_file(), f"mapped file is missing: {entry['destination']}"
        actual_hash = _sha256(destination)
        if actual_hash == entry["sha256"]:
            continue
        patch = entry.get("migration_patch")
        assert patch and patch["approved"] is True, f"unapproved migration patch: {entry['destination']}"
        assert patch["source_sha256"] == entry["sha256"]
        assert patch["patched_sha256"] == actual_hash


def test_integrity_verifier_accepts_the_recorded_backend() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/verify_reference_backend.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_swiss_lever_asset_is_separate_and_has_provenance() -> None:
    third_party_root = (
        PROJECT_ROOT
        / "src"
        / "ontology_watch_generator"
        / "third_party"
        / "grabcad"
        / "swiss_lever_watch_escapement"
    )
    assert third_party_root.is_dir()
    step_path = third_party_root / "Escapement Model.STEP"
    assert step_path.is_file()
    assert _sha256(step_path) == "313e49a2c323b84d68c2aa47df92ef0c1368338601df83cc9e320cde751c4eae"

    provenance = (PROJECT_ROOT / "THIRD_PARTY_ASSETS.md").read_text(encoding="utf-8")
    assert "GrabCAD" in provenance
    assert "Escapement Model.STEP" in provenance
    assert _sha256(step_path) in provenance
    assert "license" in provenance.lower()
    assert "distribution" in provenance.lower()

    if FROZEN_SOURCE_ROOT is None:
        return
    source_asset_root = (
        FROZEN_SOURCE_ROOT
        / "models"
        / "watch_kinematic"
        / "references"
        / "escapement"
        / "swiss_lever_grabcad_snapshot_15"
    )
    for source_asset in source_asset_root.rglob("*"):
        if source_asset.is_file():
            destination = third_party_root / source_asset.relative_to(source_asset_root)
            assert destination.is_file(), f"third-party asset is missing: {destination.name}"
            assert _sha256(destination) == _sha256(source_asset)


def test_reference_backend_contains_no_machine_local_paths() -> None:
    offenders = []
    for path in REFERENCE_BACKEND.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".md", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "C:/Users/" in text or "C:\\Users\\" in text:
            offenders.append(path.relative_to(REFERENCE_BACKEND).as_posix())
    assert offenders == []


@pytest.mark.parametrize(
    "relative_path",
    (
        "watch_kinematic/power_chain_mvp.py",
        "watch_kinematic/partitioned_bridge_stage.py",
        "watch_kinematic/pattern_card_checklist.py",
        "watch_kinematic/pattern_cards/central_hour_minute_offcenter_seconds/solver.py",
        "watch_kinematic/pattern_cards/separate_hour_minute_no_seconds/solver.py",
        "watch_kinematic/pattern_cards/pattern4_independent_hour_minute_no_seconds/solver.py",
    ),
)
def test_source_map_contains_formal_pattern_entrypoint_dependencies(relative_path: str) -> None:
    source_map = _load_source_map()
    assert relative_path in {entry["destination"] for entry in source_map["files"]}
