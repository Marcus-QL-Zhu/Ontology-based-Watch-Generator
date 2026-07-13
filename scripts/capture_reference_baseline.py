"""Capture compact reference baselines from an immutable source archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

if __package__ in {None, ""}:
    repository_root = Path(__file__).resolve().parents[1]
    if str(repository_root) not in sys.path:
        sys.path.insert(0, str(repository_root))

from scripts import reference_orchestration as orchestration


FROZEN_SOURCE_COMMIT = "5be7852844a3f4c5698a737eba81c026e96ced16"
SCHEMA_VERSION = "watch-generator-reference-baseline/v4"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIRECTORY = REPOSITORY_ROOT / "reference_baselines"
SOURCE_EVIDENCE_DIRECTORY = BASELINE_DIRECTORY / "source_evidence"
DEFAULT_SOURCE = os.environ.get("ONTOLOGY_WATCH_SOURCE")
DEFAULT_RUNTIME_ROOT = os.environ.get("ONTOLOGY_WATCH_RUNTIME_ROOT")
DEFAULT_VIEWER = os.environ.get("ONTOLOGY_WATCH_VIEWER_DIR")
EXPECTED_BUILD123D_VERSION = "0.10.0"
COMPRESSED_EVIDENCE_THRESHOLD_BYTES = 1_000_000
PRODUCT_PATTERN = re.compile(r"#\d+\s*=\s*PRODUCT\s*\(\s*'((?:''|[^'])*)'", re.IGNORECASE)
WINDOWS_USER_PATH = re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.IGNORECASE)
REQUIRED_EVIDENCE = ("solver", "semantic", "role_contracts", "motion", "kinematic", "validation")
EXTERNAL_STEP_RELATIVE_PATH = Path(
    "models/watch_kinematic/references/escapement/"
    "swiss_lever_grabcad_snapshot_15/Escapement Model.STEP"
)
CaptureFailure = orchestration.CaptureFailure

DIRECT_EVIDENCE = {
    "solver": (".solver.json", {"kind", "status", "seed", "selected_candidate"}),
    "semantic": (".semantic.json", {"kind", "status", "seed", "checks"}),
    "role_contracts": (".role_contracts.json", {"kind", "status", "roles", "contracts"}),
    "motion": (
        ".motion.json",
        {"kind", "status", "moving_groups", "fixed_features", "semantic_material_contracts", "visual_materials"},
    ),
    "kinematic": (".kinematic.json", {"kind", "status", "checks"}),
    "validation": (".validation.json", {"kind", "status", "failed_checks", "checks"}),
}

COMPLETE_REPORTS = {
    "pattern-01": "analytic_partitioned_bridge_stage_report.json",
    "pattern-02": "separate_display_partitioned_bridge_stage_report.json",
    "pattern-03": "pattern4_independent_display_complete_model_report.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", choices=sorted(orchestration.PATTERNS), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New output directory under the system temporary root.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(DEFAULT_SOURCE) if DEFAULT_SOURCE else None,
        required=DEFAULT_SOURCE is None,
        help="Read-only source worktree used only for git archive (or set ONTOLOGY_WATCH_SOURCE).",
    )
    parser.add_argument(
        "--viewer-dir",
        type=Path,
        default=Path(DEFAULT_VIEWER) if DEFAULT_VIEWER else None,
        required=DEFAULT_VIEWER is None,
        help="CAD Explorer viewer directory (or set ONTOLOGY_WATCH_VIEWER_DIR).",
    )
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=Path(DEFAULT_RUNTIME_ROOT) if DEFAULT_RUNTIME_ROOT else None,
        help=(
            "Root containing the trusted .venv/Scripts/python.exe; defaults to --source "
            "(or set ONTOLOGY_WATCH_RUNTIME_ROOT)."
        ),
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(source_root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(source_root), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _source_tree_state_sha256(source_root: Path) -> str:
    """Watch tracked, untracked, and ignored files without reading large outputs."""

    digest = hashlib.sha256()
    for path in sorted(source_root.rglob("*"), key=lambda item: item.as_posix()):
        if ".git" in path.relative_to(source_root).parts or not path.is_file():
            continue
        stat = path.stat()
        relative = path.relative_to(source_root).as_posix()
        digest.update(f"{relative}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode("utf-8"))
    return digest.hexdigest()


def source_worktree_fingerprint(source_root: Path) -> dict[str, str]:
    return {
        "head": run_git(source_root, "rev-parse", "HEAD"),
        "status": run_git(source_root, "status", "--porcelain=v1", "--untracked-files=all", "--ignored=no"),
        "tree_state_sha256": _source_tree_state_sha256(source_root),
    }


def assert_source_unchanged(before: dict[str, str], after: dict[str, str]) -> None:
    if before != after:
        raise RuntimeError("source worktree changed during baseline capture")


@contextmanager
def source_write_guard(source_root: Path) -> Iterator[dict[str, str]]:
    """Verify source immutability after both successful and failed captures."""

    before = source_worktree_fingerprint(source_root)
    try:
        yield before
    finally:
        after = source_worktree_fingerprint(source_root)
        assert_source_unchanged(before, after)


def resolve_reference_python(source_worktree: Path, runtime_root: Path | None = None) -> Path:
    selected_runtime_root = (runtime_root or source_worktree).resolve()
    reference_python = selected_runtime_root / ".venv" / "Scripts" / "python.exe"
    if not reference_python.is_file():
        raise CaptureFailure(
            "runtime root .venv interpreter is required for reference capture",
            runtime_root=str(selected_runtime_root),
            expected_interpreter=".venv/Scripts/python.exe",
        )
    return reference_python.resolve()


def materialize_external_step(source_worktree: Path, snapshot_root: Path) -> Path:
    source_step = source_worktree.resolve() / EXTERNAL_STEP_RELATIVE_PATH
    snapshot_step = snapshot_root.resolve() / EXTERNAL_STEP_RELATIVE_PATH
    if not source_step.is_file():
        raise CaptureFailure(
            "materialized external STEP is missing from source worktree",
            source_path=EXTERNAL_STEP_RELATIVE_PATH.as_posix(),
        )
    pointer_text = run_git(
        source_worktree,
        "show",
        f"{FROZEN_SOURCE_COMMIT}:{EXTERNAL_STEP_RELATIVE_PATH.as_posix()}",
    )
    pointer_hash = re.search(r"^oid sha256:([0-9a-f]{64})$", pointer_text, re.MULTILINE)
    pointer_size = re.search(r"^size ([0-9]+)$", pointer_text, re.MULTILINE)
    source_hash = sha256(source_step)
    source_size = source_step.stat().st_size
    if (
        pointer_hash is None
        or pointer_size is None
        or pointer_hash.group(1) != source_hash
        or int(pointer_size.group(1)) != source_size
    ):
        raise CaptureFailure(
            "materialized external STEP does not match the frozen LFS pointer",
            source_path=EXTERNAL_STEP_RELATIVE_PATH.as_posix(),
            materialized_sha256=source_hash,
            materialized_size_bytes=source_size,
            frozen_pointer_sha256=pointer_hash.group(1) if pointer_hash else None,
            frozen_pointer_size_bytes=int(pointer_size.group(1)) if pointer_size else None,
        )
    if not snapshot_step.is_file() or sha256(snapshot_step) != source_hash:
        shutil.copyfile(source_step, snapshot_step)
    return snapshot_step


def capture_runtime_provenance(
    reference_python: Path,
    snapshot_root: Path,
    external_step: Path,
    *,
    runtime_root_kind: str = "source_worktree_default",
) -> dict[str, str]:
    completed = subprocess.run(
        [
            str(reference_python),
            "-c",
            (
                "import json, platform, sys, build123d; "
                "print(json.dumps({'python_executable': sys.executable, "
                "'python_version': platform.python_version(), "
                "'build123d_version': build123d.__version__}))"
            ),
        ],
        cwd=snapshot_root,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(snapshot_root),
        },
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise CaptureFailure(
            "runtime root .venv provenance probe failed",
            stderr=completed.stderr.strip(),
        )
    try:
        versions = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as error:
        raise CaptureFailure("runtime root .venv provenance was not structured") from error
    observed_python = versions.get("python_executable")
    if not isinstance(observed_python, str) or Path(observed_python).resolve() != reference_python.resolve():
        raise CaptureFailure(
            "runtime interpreter provenance does not match the selected interpreter",
            expected_interpreter=str(reference_python.resolve()),
            observed_interpreter=observed_python,
        )
    observed_build123d = versions.get("build123d_version")
    if observed_build123d != EXPECTED_BUILD123D_VERSION:
        raise CaptureFailure(
            "runtime build123d version is not trusted for reference capture",
            expected_build123d_version=EXPECTED_BUILD123D_VERSION,
            observed_build123d_version=observed_build123d,
        )
    return {
        "source_code_root": "frozen_git_archive_snapshot",
        "runtime_root": runtime_root_kind,
        "python_executable": ".venv/Scripts/python.exe",
        "python_version": versions["python_version"],
        "build123d_version": observed_build123d,
        "materialized_external_step_path": EXTERNAL_STEP_RELATIVE_PATH.as_posix(),
        "materialized_external_step_sha256": sha256(external_step),
    }


def ensure_new_system_temporary_directory(output: Path) -> Path:
    resolved = output.resolve()
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if not resolved.is_relative_to(temporary_root):
        raise ValueError(f"generation output must be inside the system temporary directory: {temporary_root}")
    if resolved.exists():
        raise ValueError("generation output directory must be newly created and empty")
    resolved.mkdir(parents=True)
    return resolved


@contextmanager
def short_system_temporary_root() -> Iterator[Path]:
    """Use a temporary ``subst`` drive so archive paths stay below Win32 limits."""

    root = Path(tempfile.gettempdir())
    if os.name != "nt":
        yield root
        return
    drive = next((f"{letter}:" for letter in "ZYXWVUTSRQPONMLKJIHGFED" if not Path(f"{letter}:/").exists()), None)
    if drive is None:
        raise RuntimeError("no unused drive letter is available for the temporary source snapshot")
    subprocess.run(["subst", drive, str(root)], check=True)
    try:
        yield Path(f"{drive}/")
    finally:
        subprocess.run(["subst", drive, "/D"], check=False)


def extract_frozen_source(source_root: Path, destination: Path) -> None:
    resolved = run_git(source_root, "rev-parse", FROZEN_SOURCE_COMMIT)
    if resolved != FROZEN_SOURCE_COMMIT:
        raise RuntimeError(f"source commit resolved to {resolved}, not {FROZEN_SOURCE_COMMIT}")
    archive = subprocess.run(
        ["git", "-C", str(source_root), "archive", "--format=tar", FROZEN_SOURCE_COMMIT],
        check=True,
        capture_output=True,
    )
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
        for member in tar.getmembers():
            if not (destination / member.name).resolve().is_relative_to(root):
                raise RuntimeError(f"unsafe git archive member: {member.name}")
        tar.extractall(destination, filter="data")


def classify_artifact(filename: str, postprocessed: dict[str, str]) -> dict[str, str]:
    if filename in postprocessed:
        return {"classification": "derived", "derivation": "postprocessed_by_browser_sync"}
    if filename.lower().endswith(".glb"):
        return {"classification": "derived", "derivation": "step_to_glb"}
    return {"classification": "source_native", "derivation": "direct_source_output"}


def collect_output_artifacts(
    output_dir: Path,
    postprocessed: dict[str, str],
) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    paths = (candidate for candidate in output_dir.rglob("*") if candidate.is_file())
    for path in sorted(paths, key=lambda item: item.as_posix()):
        relative = path.relative_to(output_dir)
        if relative.parts[0] == "_source_native_json" or path.suffix.lower() == ".png":
            continue
        filename = relative.as_posix()
        classification = classify_artifact(filename, postprocessed)
        artifacts.append({
            "filename": filename,
            "sha256": sha256(path),
            "size_bytes": path.stat().st_size,
            **classification,
        })
    return artifacts


def collect_step_occurrences(step: Path) -> list[dict[str, str]]:
    text = step.read_text(encoding="utf-8", errors="replace")
    labels = {
        match.group(1).replace("''", "'")
        for match in PRODUCT_PATTERN.finditer(text)
        if match.group(1)
    }
    return [{"label": label, "source": "ISO-10303-21 PRODUCT"} for label in sorted(labels)]


def portable_stage_fingerprint(
    fingerprint: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """Replace validated runtime-absolute artifact paths with run-relative paths."""

    portable = dict(fingerprint)
    output_root = output_dir.resolve()
    for field in ("output_step_path", "input_artifact_path"):
        value = portable.get(field)
        if value is None:
            continue
        path = Path(value)
        if not path.is_absolute():
            raise ValueError(f"stage fingerprint {field} must be absolute before archival")
        resolved = path.resolve()
        if not resolved.is_relative_to(output_root):
            raise ValueError(f"stage fingerprint {field} is outside the capture output directory")
        portable[field] = resolved.relative_to(output_root).as_posix()
    return portable


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _absent(reason: str) -> dict[str, Any]:
    return {
        "status": "absent",
        "value": None,
        "classification": "source_native",
        "reason": reason,
    }


def discover_native_evidence(
    output_dir: Path,
    pattern_id: str,
    *,
    final_step: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Find only exact direct sidecars or approved top-level report nodes."""

    source_root = output_dir / "_source_native_json"
    if not source_root.is_dir():
        source_root = output_dir
    files = sorted(path for path in source_root.glob("*.json") if path.is_file())
    evidence: dict[str, dict[str, Any]] = {}
    for kind, (suffix, required_fields) in DIRECT_EVIDENCE.items():
        valid = []
        for path in files:
            if not path.name.endswith(suffix):
                continue
            payload = _load_json(path)
            if payload is not None and required_fields <= set(payload):
                valid.append((path, payload))
        if valid:
            selected = valid
            if final_step is not None and kind == "motion":
                final_sidecar_name = f"{final_step.stem}{suffix}"
                final_bound = [item for item in valid if item[0].name == final_sidecar_name]
                if final_bound:
                    selected = final_bound
            canonical_payloads = {
                json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                for _, payload in selected
            }
            if len(canonical_payloads) != 1:
                raise CaptureFailure(
                    "conflicting native evidence sidecars matched one evidence kind",
                    evidence_kind=kind,
                    source_filenames=[path.name for path, _ in selected],
                )
            path, payload = selected[0]
            preservation = "byte_for_byte_copy"
            archived_payload = payload
            json_pointer = ""
            if kind == "solver":
                selected_keys = (
                    "kind", "pattern_card_id", "status", "seed", "selection_strategy",
                    "candidate_count", "feasible_candidate_count", "selected_candidate",
                )
                archived_payload = {key: payload[key] for key in selected_keys if key in payload}
                preservation = "lossless_selected_top_level_fields"
                json_pointer = "/{kind,pattern_card_id,status,seed,selection_strategy,candidate_count,feasible_candidate_count,selected_candidate}"
            evidence[kind] = {
                "status": "captured",
                "classification": "source_native",
                "preservation": preservation,
                "source_filename": path.name,
                "json_pointer": json_pointer,
                "schema_fields": sorted(required_fields),
                "_source_path": path,
                "_payload": archived_payload,
            }
        else:
            evidence[kind] = _absent(
                f"no direct {suffix} sidecar matched the exact source schema"
            )

    if pattern_id == "pattern-03":
        report_name = COMPLETE_REPORTS[pattern_id]
        report_path = source_root / report_name
        report = _load_json(report_path)
        embedded = report.get("evidence") if report else None
        if isinstance(embedded, dict):
            for kind in ("solver", "semantic", "role_contracts", "kinematic"):
                wrapper = embedded.get(kind)
                required = DIRECT_EVIDENCE[kind][1]
                if not isinstance(wrapper, dict):
                    continue
                payload = wrapper.get("payload")
                provenance = wrapper.get("source")
                if not isinstance(payload, dict) or not isinstance(provenance, dict):
                    raise CaptureFailure(
                        "Pattern 3 embedded evidence wrapper is malformed",
                        evidence_kind=kind,
                        source_filename=report_name,
                    )
                if not required <= set(payload):
                    raise CaptureFailure(
                        "Pattern 3 embedded evidence payload does not match the exact source schema",
                        evidence_kind=kind,
                        source_filename=report_name,
                    )
                if evidence[kind]["status"] == "captured":
                    raise CaptureFailure(
                        "Pattern 3 has both direct and embedded evidence for one kind",
                        evidence_kind=kind,
                        source_filename=report_name,
                    )
                evidence[kind] = {
                    "status": "captured",
                    "classification": "source_native",
                    "preservation": "lossless_json_subtree_extract",
                    "source_filename": report_name,
                    "json_pointer": f"/evidence/{kind}/payload",
                    "schema_fields": sorted(required),
                    "provenance": provenance,
                    "_source_path": report_path,
                    "_payload": payload,
                }

    if evidence["validation"]["status"] != "captured" and pattern_id == "pattern-03":
        report_name = COMPLETE_REPORTS[pattern_id]
        report_path = source_root / report_name
        report = _load_json(report_path)
        validation = report.get("validation") if report else None
        required = DIRECT_EVIDENCE["validation"][1]
        if isinstance(validation, dict) and required <= set(validation):
            evidence["validation"] = {
                "status": "captured",
                "classification": "source_native",
                "preservation": "lossless_json_subtree_extract",
                "source_filename": report_name,
                "json_pointer": "/validation",
                "schema_fields": sorted(required),
                "_source_path": report_path,
                "_payload": validation,
            }

    report_name = COMPLETE_REPORTS.get(pattern_id)
    report_path = source_root / report_name if report_name else None
    report = _load_json(report_path) if report_path else None
    if report:
        selected = {
            key: report[key]
            for key in (
                "kind", "pattern_card_id", "status", "seed", "layout_id", "generation_gate",
                "validation", "bridge_stage", "lightening_enabled",
            )
            if key in report
        }
        evidence["complete_geometry_report"] = {
            "status": "captured",
            "classification": "source_native",
            "preservation": "lossless_selected_top_level_fields",
            "source_filename": report_name,
            "json_pointer": "/{kind,status,seed,layout_id,generation_gate,validation,bridge_stage,lightening_enabled}",
            "schema_fields": sorted(selected),
            "_source_path": report_path,
            "_payload": selected,
        }

    checklist_path = source_root / "checklist.json"
    checklist = _load_json(checklist_path)
    if checklist:
        selected = {
            key: checklist[key]
            for key in ("kind", "pattern_card_id", "seed", "status", "items", "failed_items")
            if key in checklist
        }
        evidence["bridge_checklist"] = {
            "status": "captured",
            "classification": "source_native",
            "preservation": "lossless_selected_top_level_fields",
            "source_filename": checklist_path.name,
            "json_pointer": "/{kind,pattern_card_id,seed,status,items,failed_items}",
            "schema_fields": sorted(selected),
            "_source_path": checklist_path,
            "_payload": selected,
        }
    return evidence


def missing_required_evidence(evidence: dict[str, dict[str, Any]]) -> list[str]:
    return sorted(kind for kind in REQUIRED_EVIDENCE if evidence.get(kind, {}).get("status") != "captured")


def validate_evidence_identity(
    evidence: dict[str, dict[str, Any]],
    *,
    requested_seed: int,
    source_pattern_id: str,
) -> None:
    """Bind Pattern 2 native evidence, report, and checklist to one run identity."""

    seed_required = {"solver", "semantic", "complete_geometry_report", "bridge_checklist"}
    for kind, item in evidence.items():
        if item.get("status") != "captured":
            continue
        payload = item.get("_payload")
        if not isinstance(payload, dict):
            raise CaptureFailure("captured evidence lacks a structured payload", evidence_kind=kind)
        if kind in seed_required and payload.get("seed") != requested_seed:
            raise CaptureFailure(
                "captured evidence seed differs from the requested run seed",
                evidence_kind=kind,
                expected_seed=requested_seed,
                observed_seed=payload.get("seed"),
            )
        if payload.get("pattern_card_id") != source_pattern_id:
            raise CaptureFailure(
                "captured evidence pattern_card_id differs from the source run pattern",
                evidence_kind=kind,
                expected_pattern_card_id=source_pattern_id,
                observed_pattern_card_id=payload.get("pattern_card_id"),
            )


def validate_pattern3_complete_evidence_identity(
    evidence: dict[str, dict[str, Any]],
    *,
    requested_seed: int,
    complete_entrypoint_pattern_card_id: str,
) -> None:
    """Bind Pattern 3 embedded complete-report evidence to its one source run."""

    for kind in ("solver", "semantic", "role_contracts", "kinematic"):
        item = evidence.get(kind)
        if not isinstance(item, dict) or item.get("status") != "captured":
            raise CaptureFailure("Pattern 3 required evidence was not captured", evidence_kind=kind)
        payload = item.get("_payload")
        provenance = item.get("provenance")
        if not isinstance(payload, dict) or not isinstance(provenance, dict):
            raise CaptureFailure("Pattern 3 embedded evidence lacks payload or provenance", evidence_kind=kind)
        if provenance.get("complete_entrypoint_pattern_card_id") != complete_entrypoint_pattern_card_id:
            raise CaptureFailure(
                "Pattern 3 embedded evidence complete entrypoint differs from the source run pattern",
                evidence_kind=kind,
                expected_pattern_card_id=complete_entrypoint_pattern_card_id,
                observed_pattern_card_id=provenance.get("complete_entrypoint_pattern_card_id"),
            )
        if provenance.get("generation_seed") != requested_seed:
            raise CaptureFailure(
                "Pattern 3 embedded evidence generation seed differs from the requested run seed",
                evidence_kind=kind,
                expected_seed=requested_seed,
                observed_seed=provenance.get("generation_seed"),
            )
        if not isinstance(provenance.get("builder"), str) or not provenance["builder"]:
            raise CaptureFailure("Pattern 3 embedded evidence has no source builder", evidence_kind=kind)
        payload_card = payload.get("pattern_card_id")
        if payload_card is not None and provenance.get("payload_pattern_card_id") != payload_card:
            raise CaptureFailure(
                "Pattern 3 embedded evidence payload pattern identity differs from provenance",
                evidence_kind=kind,
                payload_pattern_card_id=payload_card,
                provenance_pattern_card_id=provenance.get("payload_pattern_card_id"),
            )
        payload_seed = payload.get("seed")
        if payload_seed is not None and payload_seed != requested_seed:
            raise CaptureFailure(
                "Pattern 3 embedded evidence payload seed differs from the requested run seed",
                evidence_kind=kind,
                expected_seed=requested_seed,
                observed_seed=payload_seed,
            )


def archive_native_evidence(
    pattern_id: str,
    evidence: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    destination_root = SOURCE_EVIDENCE_DIRECTORY / pattern_id
    if destination_root.exists():
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True)
    archived: dict[str, dict[str, Any]] = {}
    for kind, item in evidence.items():
        public = {key: value for key, value in item.items() if not key.startswith("_")}
        if item["status"] != "captured":
            archived[kind] = public
            continue
        if item["preservation"] == "byte_for_byte_copy":
            raw_bytes = Path(item["_source_path"]).read_bytes()
        else:
            raw_bytes = (
                json.dumps(item["_payload"], ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
        content = raw_bytes.decode("utf-8")
        if WINDOWS_USER_PATH.search(content):
            raise RuntimeError(f"source evidence leaks an absolute user path: {kind}")
        if len(raw_bytes) > COMPRESSED_EVIDENCE_THRESHOLD_BYTES:
            destination = destination_root / f"{kind}.json.gz"
            destination.write_bytes(gzip.compress(raw_bytes, mtime=0))
            encoding = "gzip"
        else:
            destination = destination_root / f"{kind}.json"
            destination.write_bytes(raw_bytes)
            encoding = "utf-8"
        public.update({
            "project_relative_path": destination.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": sha256(destination),
            "size_bytes": destination.stat().st_size,
            "encoding": encoding,
            "uncompressed_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "uncompressed_size_bytes": len(raw_bytes),
        })
        archived[kind] = public
    return archived


def capture_screenshots(pattern_id: str, output_dir: Path, final_step: Path, viewer_dir: Path) -> list[dict[str, Any]]:
    if not viewer_dir.is_dir():
        raise RuntimeError(f"CAD Explorer viewer is unavailable: {viewer_dir}")
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm is required for browser review screenshots")
    target_dir = BASELINE_DIRECTORY / "screenshots"
    target_dir.mkdir(parents=True, exist_ok=True)
    screenshots = []
    for view, camera in (("top", "top"), ("isometric", "iso")):
        temporary = output_dir / f"{pattern_id.replace('-', '_')}_{view}.png"
        subprocess.run(
            [npm, "--prefix", str(viewer_dir), "run", "snapshot", "--", "--no-daemon", "--workspace-root", str(output_dir.parent), "--root-dir", output_dir.name, "--input", str(final_step), "--output", str(temporary), "--theme", "technical", "--camera", camera, "--view-labels", "--size-profile", "assembly"],
            check=True,
            capture_output=True,
            text=True,
        )
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError(f"browser review did not create the {view} screenshot")
        destination = target_dir / temporary.name
        shutil.copy2(temporary, destination)
        screenshots.append({
            "view": view,
            "filename": destination.name,
            "sha256": sha256(destination),
            "size_bytes": destination.stat().st_size,
            "classification": "derived",
            "derivation": "cad_explorer_snapshot",
        })
    return screenshots


def _spec9_coverage(
    source_evidence: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    def evidence_path(kind: str, pointers: str) -> str:
        item = source_evidence.get(kind, {})
        path = item.get("project_relative_path")
        return f"{path}{pointers}" if path else f"missing:{kind}"

    return {
        "occurrences": ["baseline.step_occurrences (ISO-10303-21 PRODUCT labels)"],
        "roles": [evidence_path("role_contracts", "#/roles,#/contracts")],
        "materials_and_transparency": [
            evidence_path("motion", "#/semantic_material_contracts,#/visual_materials")
        ],
        "axes_gears_bridges_and_screws": [
            "baseline.stages[*].stage_fingerprint#/axes,#/gears",
            evidence_path("complete_geometry_report", "#/bridge_stage/bridges"),
        ],
        "motion_target_axis_ratio_direction": [
            evidence_path("motion", "#/moving_groups,#/direction_contract,#/display_motion_works")
        ],
        "validation_checks_reasons_and_status": [
            evidence_path("validation", "#/status,#/failed_checks,#/checks"),
            evidence_path("complete_geometry_report", "#/status,#/validation,#/bridge_stage"),
        ],
    }


def build_record(
    *,
    pattern_id: str,
    seed: int,
    output_dir: Path,
    result: dict[str, Any],
    source_unchanged: bool,
    viewer_dir: Path,
) -> dict[str, Any]:
    plan = orchestration.PATTERNS[pattern_id]
    final_step = Path(result["final_step"])
    orchestration.validate_orchestration_result(plan, result, requested_seed=seed)
    stages = []
    for planned, observed in zip(plan.stages, result["stages"], strict=True):
        stages.append({
            "name": planned.name,
            "entrypoint": planned.entrypoint,
            "invocation": planned.invocation,
            "role": planned.role,
            "classification": planned.classification,
            "policy": "required_pass",
            "status": observed["status"],
            "artifact_filenames": observed.get("artifact_filenames", {}),
            "stage_fingerprint": portable_stage_fingerprint(
                observed["stage_fingerprint"], output_dir
            ),
        })

    source_fingerprints = [
        stage["stage_fingerprint"] for stage in stages if stage["classification"] == orchestration.SOURCE_NATIVE
    ]
    resolved_seed = source_fingerprints[0]["resolved_seed"]
    final_step_sha256 = orchestration.validate_final_step_identity(result, output_dir)
    if result.get("final_step_sha256") != final_step_sha256:
        raise CaptureFailure(
            "run record final STEP hash differs from the validated final artifact",
            recorded_sha256=result.get("final_step_sha256"),
            observed_sha256=final_step_sha256,
        )
    artifacts = collect_output_artifacts(output_dir, result.get("postprocessed_artifacts", {}))
    evidence = discover_native_evidence(output_dir, pattern_id, final_step=final_step)
    if pattern_id == "pattern-02":
        validate_evidence_identity(
            evidence,
            requested_seed=seed,
            source_pattern_id=source_fingerprints[0]["source_pattern_id"],
        )
    elif pattern_id == "pattern-03":
        validate_pattern3_complete_evidence_identity(
            evidence,
            requested_seed=seed,
            complete_entrypoint_pattern_card_id=source_fingerprints[0]["source_pattern_id"],
        )
    source_evidence = archive_native_evidence(pattern_id, evidence)
    screenshots = capture_screenshots(pattern_id, output_dir, final_step, viewer_dir)
    artifacts.extend({
        "filename": f"screenshots/{item['filename']}",
        "sha256": item["sha256"],
        "size_bytes": item["size_bytes"],
        "classification": "derived",
        "derivation": item["derivation"],
    } for item in screenshots)
    missing = missing_required_evidence(source_evidence)
    if not source_unchanged:
        missing.append("source_worktree_unchanged")
    occurrences = collect_step_occurrences(final_step)
    if not occurrences:
        missing.append("step_occurrences")

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "baseline_id": f"{pattern_id}-seed-{seed}",
        "status": "pass" if not missing else "failed",
        "pattern_id": pattern_id,
        "requested_seed": seed,
        "resolved_seed": resolved_seed,
        "same_run_directory": True,
        "final_step": {
            "filename": final_step.name,
            "sha256": final_step_sha256,
            "occurrence_inventory_status": "pass",
            "expected_occurrence_count": sum(result["expected_final_occurrence_counts"].values()),
            "expected_label_count": len(result["expected_final_occurrence_counts"]),
            "expected_occurrence_counts": result["expected_final_occurrence_counts"],
        },
        "runtime_provenance": result["runtime_provenance"],
        "final_external_envelope": {
            "expected": result["expected_final_envelope"],
            "expected_external_occurrences": result["expected_external_occurrences"],
            "violations": result["final_external_envelope_violations"],
        },
        "source": {
            "commit": FROZEN_SOURCE_COMMIT,
            "source_pattern_id": plan.source_pattern_id,
            "worktree_unchanged": source_unchanged,
            "execution_boundary": "git archive snapshot only",
            "write_guard": "HEAD + git status + tracked/untracked/ignored file metadata digest",
        },
        "stages": stages,
        "artifacts": artifacts,
        "artifact_classes": {
            "source_native": [item["filename"] for item in artifacts if item["classification"] == "source_native"],
            "derived": [item["filename"] for item in artifacts if item["classification"] == "derived"],
            "normalized": ["stage_fingerprints", "spec9_coverage"],
        },
        "step_occurrences": occurrences,
        "source_evidence": source_evidence,
        "spec9_coverage": _spec9_coverage(source_evidence),
        "screenshots": {"status": "captured", "artifacts": screenshots},
    }
    if missing:
        record["failure"] = {
            "kind": "source_baseline_contract_failure",
            "missing_evidence": sorted(set(missing)),
            "message": "The capture refuses to infer missing source-native evidence or promote a failed stage.",
        }
    return record


def main() -> int:
    args = parse_args()
    try:
        output_dir = ensure_new_system_temporary_directory(args.output)
        source_root = args.source.resolve()
        with source_write_guard(source_root):
            reference_python = resolve_reference_python(source_root, args.runtime_root)
            runtime_root_kind = (
                "explicit_runtime_root" if args.runtime_root is not None
                else "source_worktree_default"
            )
            with short_system_temporary_root() as snapshot_parent:
                with tempfile.TemporaryDirectory(prefix="watch-reference-", dir=snapshot_parent) as snapshot_dir:
                    snapshot = Path(snapshot_dir)
                    extract_frozen_source(source_root, snapshot)
                    external_step = materialize_external_step(source_root, snapshot)
                    runtime_provenance = capture_runtime_provenance(
                        reference_python,
                        snapshot,
                        external_step,
                        runtime_root_kind=runtime_root_kind,
                    )
                    result = orchestration.run_formal_chain(
                        snapshot,
                        output_dir,
                        args.pattern,
                        args.seed,
                        reference_python,
                    )
                    result["runtime_provenance"] = runtime_provenance
            record = build_record(
                pattern_id=args.pattern,
                seed=args.seed,
                output_dir=output_dir,
                result=result,
                source_unchanged=True,
                viewer_dir=args.viewer_dir,
            )
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError, tarfile.TarError) as error:
        print(f"reference baseline capture failed: {error}", file=sys.stderr)
        return 1

    BASELINE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    path = BASELINE_DIRECTORY / f"{args.pattern.replace('-', '_')}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if record["status"] != "pass":
        print(
            f"reference baseline captured as failed: {', '.join(record['failure']['missing_evidence'])}",
            file=sys.stderr,
        )
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
