"""Execute compact, source-observed watch baseline orchestration chains."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RESULT_MARKER = "__WATCH_ORCHESTRATION_RESULT__="
PRODUCT_PATTERN = re.compile(r"#\d+\s*=\s*PRODUCT\s*\(\s*'((?:''|[^'])*)'", re.IGNORECASE)
SOURCE_NATIVE = "source_native"
DERIVED = "derived"
FINAL_ESCAPEMENT_ENVELOPES = {
    "pattern-02": {"x": [-22.0, 22.0], "y": [-22.0, 22.0], "z": [-0.675, 5.16]},
}
FINAL_EXTERNAL_OCCURRENCE_INVENTORIES = {
    "pattern-02": (
        "external_balance_replacement_staff",
        "external_balance_upper_jewel_bearing",
        "external_balance_wheel",
        "external_escape_staff",
        "external_escape_upper_cap",
        "external_escape_upper_fixed_hardware",
        "external_escape_wheel",
        "external_escapement_auxiliary_solid_06",
        "external_escapement_auxiliary_solid_07",
        "external_escapement_auxiliary_solid_08",
        "external_escapement_auxiliary_solid_09",
        "external_escapement_auxiliary_solid_12",
        "external_escapement_auxiliary_solid_13",
        "external_escapement_auxiliary_solid_16",
        "external_escapement_auxiliary_solid_17",
        "external_escapement_auxiliary_solid_19",
        "external_escapement_auxiliary_solid_20",
        "external_escapement_auxiliary_solid_21",
        "external_escapement_auxiliary_solid_22",
        "external_escapement_auxiliary_solid_23",
        "external_escapement_auxiliary_solid_24",
        "external_escapement_auxiliary_solid_25",
        "external_escapement_auxiliary_solid_26",
        "external_escapement_auxiliary_solid_27",
        "external_escapement_auxiliary_solid_28",
        "external_escapement_auxiliary_solid_29",
        "external_escapement_auxiliary_solid_30",
        "external_escapement_auxiliary_solid_31",
        "external_escapement_auxiliary_solid_32",
        "external_escapement_auxiliary_solid_33",
        "external_escapement_auxiliary_solid_34",
        "external_escapement_reference_plate",
        "external_hairspring",
        "external_pallet_fork",
    ),
}
FINAL_OCCURRENCE_INVENTORIES = {
    "pattern-02": (
        "ASSEMBLY",
        "arbor_display_input_relay_axis",
        "arbor_display_relay_axis",
        "arbor_hour_display_axis",
        "arbor_minute_display_axis",
        "arbor_train_stage_1_axis",
        "arbor_train_stage_2_axis",
        "arbor_train_stage_3_axis",
        "barrel_arbor",
        "barrel_bridge",
        "barrel_bridge_service_1_screw_1",
        "barrel_bridge_service_1_screw_2",
        "barrel_bridge_service_1_screw_3",
        "barrel_drum",
        "barrel_outer_teeth",
        "display_input_relay_compound_member",
        "display_input_relay_pinion",
        "display_input_relay_wheel_hub",
        "display_input_relay_wheel_tooth_profile",
        "display_relay_compound_member",
        "display_relay_pinion",
        "display_relay_wheel_hub",
        "display_relay_wheel_tooth_profile",
        "escape_arbor",
        "escape_pinion",
        "escapement_bridge",
        "escapement_bridge_service_1_screw_1",
        "escapement_bridge_service_1_screw_2",
        *FINAL_EXTERNAL_OCCURRENCE_INVENTORIES["pattern-02"],
        "foundation_mainplate",
        "hour_display_member",
        "hour_display_member_hub",
        "hour_hand_arbor_extension",
        "hour_hand_blade",
        "hour_hand_hub",
        "lower_jewel_barrel_axis",
        "lower_jewel_display_input_relay_axis",
        "lower_jewel_display_relay_axis",
        "lower_jewel_escape_axis",
        "lower_jewel_hour_display_axis",
        "lower_jewel_minute_display_axis",
        "lower_jewel_seat_barrel_axis",
        "lower_jewel_seat_display_input_relay_axis",
        "lower_jewel_seat_display_relay_axis",
        "lower_jewel_seat_escape_axis",
        "lower_jewel_seat_hour_display_axis",
        "lower_jewel_seat_minute_display_axis",
        "lower_jewel_seat_train_stage_1_axis",
        "lower_jewel_seat_train_stage_2_axis",
        "lower_jewel_seat_train_stage_3_axis",
        "lower_jewel_train_stage_1_axis",
        "lower_jewel_train_stage_2_axis",
        "lower_jewel_train_stage_3_axis",
        "minute_display_member",
        "minute_display_member_hub",
        "minute_hand_arbor_extension",
        "minute_hand_blade",
        "minute_hand_hub",
        "SOLID",
        "train_bridge",
        "train_bridge_service_1_screw_1",
        "train_bridge_service_1_screw_2",
        "train_bridge_service_1_screw_3",
        "train_stage_1_pinion_hub",
        "train_stage_1_pinion_tooth_profile",
        "train_stage_1_wheel",
        "train_stage_2_pinion_hub",
        "train_stage_2_pinion_tooth_profile",
        "train_stage_2_wheel",
        "train_stage_3_pinion_hub",
        "train_stage_3_pinion_tooth_profile",
        "train_stage_3_wheel",
        "upper_jewel_bearing_barrel_axis",
        "upper_jewel_bearing_display_input_relay_axis",
        "upper_jewel_bearing_display_relay_axis",
        "upper_jewel_bearing_escape_axis",
        "upper_jewel_bearing_hour_display_axis",
        "upper_jewel_bearing_minute_display_axis",
        "upper_jewel_bearing_train_stage_1_axis",
        "upper_jewel_bearing_train_stage_2_axis",
        "upper_jewel_bearing_train_stage_3_axis",
        "upper_pivot_barrel_axis",
        "upper_pivot_display_input_relay_axis",
        "upper_pivot_display_relay_axis",
        "upper_pivot_escape_axis",
        "upper_pivot_hour_display_axis",
        "upper_pivot_minute_display_axis",
        "upper_pivot_train_stage_1_axis",
        "upper_pivot_train_stage_2_axis",
        "upper_pivot_train_stage_3_axis",
        "watch_power_chain_separate_display_analytic_partitioned_bridges",
    ),
}
FINAL_OCCURRENCE_COUNT_INVENTORIES = {
    "pattern-02": {
        label: 79 if label == "ASSEMBLY" else 126 if label == "SOLID" else 1
        for label in FINAL_OCCURRENCE_INVENTORIES["pattern-02"]
    },
}


class CaptureFailure(RuntimeError):
    """A capture failure with machine-readable evidence."""

    def __init__(self, message: str, **details: Any) -> None:
        self.message = message
        self.details = details
        super().__init__(json.dumps({"message": message, **details}, sort_keys=True))


@dataclass(frozen=True)
class Stage:
    name: str
    entrypoint: str
    invocation: str
    role: str
    classification: str = SOURCE_NATIVE


@dataclass(frozen=True)
class PatternPlan:
    pattern_id: str
    source_pattern_id: str
    stages: tuple[Stage, ...]


POWER_CHAIN = "models.watch_kinematic.watch_kinematic.power_chain_mvp.run_power_chain_mvp"
BRIDGES = "models.watch_kinematic.watch_kinematic.partitioned_bridge_stage"
CHECKLIST = "models.watch_kinematic.watch_kinematic.pattern_card_checklist.write_pattern2_checklist_artifacts"
STEP_CONVERTER = "skills.cad.scripts.step.cli.main"
SYNC = f"{BRIDGES}.sync_browser_bridge_translucency_artifacts"

PATTERNS = {
    "pattern-01": PatternPlan(
        "pattern-01",
        "central_hour_minute_offcenter_seconds",
        (
            Stage("base_engineering_evidence", POWER_CHAIN, "run_power_chain_mvp(output_dir, seed=seed)", "base_evidence"),
            Stage("final_analytic_partitioned_bridge_complete_stage", f"{BRIDGES}.build_partitioned_bridge_stage", "build_partitioned_bridge_stage(output_dir, seed=seed, layout_id=..., include_lightening=True)", "final_complete_bridge_model"),
            Stage("step_to_glb", STEP_CONVERTER, "step --kind assembly <final-step>", "artifact_conversion", DERIVED),
            Stage("browser_sync", SYNC, "sync_browser_bridge_translucency_artifacts(final_step)", "browser_sync", DERIVED),
        ),
    ),
    "pattern-02": PatternPlan(
        "pattern-02",
        "separate_hour_minute_no_seconds",
        (
            Stage("base_engineering_evidence", POWER_CHAIN, "run_power_chain_mvp(output_dir, seed=seed, pattern_card_id=PATTERN_CARD_ID)", "base_evidence"),
            Stage("complete_partitioned_bridge_stage", f"{BRIDGES}.build_separate_display_partitioned_bridge_stage", "build_separate_display_partitioned_bridge_stage(output_dir, seed=seed, include_lightening=True)", "final_complete_bridge_model"),
            Stage("bridge_checklist", CHECKLIST, "write_pattern2_checklist_artifacts(output_dir, seed=seed)", "bridge_checklist"),
            Stage("step_to_glb", STEP_CONVERTER, "step --kind assembly <final-step>", "artifact_conversion", DERIVED),
            Stage("browser_sync", SYNC, "sync_browser_bridge_translucency_artifacts(final_step)", "browser_sync", DERIVED),
        ),
    ),
    "pattern-03": PatternPlan(
        "pattern-03",
        "pattern4_independent_hour_minute_no_seconds",
        (
            Stage("former_pattern4_hard_gated_complete_entry", f"{BRIDGES}.build_pattern4_independent_display_complete_model", "build_pattern4_independent_display_complete_model(output_dir, seed=seed, include_lightening=True)", "complete_model"),
            Stage("step_to_glb", STEP_CONVERTER, "step --kind assembly <final-step>", "artifact_conversion", DERIVED),
            Stage("browser_sync", SYNC, "sync_browser_bridge_translucency_artifacts(final_step)", "browser_sync", DERIVED),
        ),
    ),
}


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def make_source_stage_fingerprint(
    *,
    stage_name: str,
    requested_seed: int,
    resolved_seed: int | None,
    pattern_id: str,
    source_pattern_id: str | None,
    candidate_id: str | None,
    axes: list[dict[str, Any]] | None,
    gears: list[dict[str, Any]] | None,
    bridge_layout_id: str | None,
    bridge_layout_reason: str | None,
    output_step_name: str | None,
) -> dict[str, Any]:
    """Build a compact fingerprint from values observed by one source stage."""

    unavailable: dict[str, str] = {}
    if bridge_layout_id is None:
        unavailable["bridge_layout_id"] = bridge_layout_reason or "stage did not emit a bridge layout"
    if output_step_name is None:
        unavailable["output_step_name"] = "stage did not emit a STEP artifact"
    core = {
        "resolved_seed": resolved_seed,
        "pattern_id": pattern_id,
        "source_pattern_id": source_pattern_id,
        "candidate_id": candidate_id,
        "axes": axes,
        "gears": gears,
    }
    return {
        "observation_kind": "source_design",
        "stage_name": stage_name,
        "requested_seed": requested_seed,
        **core,
        "design_digest": _canonical_sha256(core),
        "bridge_layout_id": bridge_layout_id,
        "output_step_name": output_step_name,
        "unavailable_reasons": unavailable,
    }


def make_derived_stage_fingerprint(
    *,
    stage_name: str,
    requested_seed: int,
    input_artifact: str,
    input_sha256: str,
    output_artifact: str,
    output_sha256: str,
) -> dict[str, Any]:
    reason = "derived artifact stage does not emit or resolve source design fields"
    unavailable_fields = (
        "resolved_seed", "candidate_id", "axes", "gears", "design_digest", "bridge_layout_id"
    )
    return {
        "observation_kind": "artifact_lineage",
        "stage_name": stage_name,
        "requested_seed": requested_seed,
        "resolved_seed": None,
        "pattern_id": None,
        "source_pattern_id": None,
        "candidate_id": None,
        "axes": None,
        "gears": None,
        "design_digest": None,
        "bridge_layout_id": None,
        "output_step_name": None,
        "input_artifact": input_artifact,
        "input_sha256": input_sha256,
        "output_artifact": output_artifact,
        "output_sha256": output_sha256,
        "unavailable_reasons": {field: reason for field in unavailable_fields},
    }


def validate_formal_chain(plan: PatternPlan) -> None:
    if not plan.stages:
        raise ValueError("formal orchestration chain cannot be empty")
    complete = [stage for stage in plan.stages if stage.role == "complete_model"]
    raw_complete_entrypoints = {
        POWER_CHAIN,
        f"{BRIDGES}.build_partitioned_bridge_stage",
        f"{BRIDGES}.build_separate_display_partitioned_bridge_stage",
    }
    if any(stage.entrypoint in raw_complete_entrypoints for stage in complete):
        raise ValueError("a raw base runner or bridge builder is not a complete-model entrypoint")
    expected = {
        "pattern-01": ["base_engineering_evidence", "final_analytic_partitioned_bridge_complete_stage", "step_to_glb", "browser_sync"],
        "pattern-02": ["base_engineering_evidence", "complete_partitioned_bridge_stage", "bridge_checklist", "step_to_glb", "browser_sync"],
        "pattern-03": ["former_pattern4_hard_gated_complete_entry", "step_to_glb", "browser_sync"],
    }.get(plan.pattern_id)
    if expected is None or [stage.name for stage in plan.stages] != expected:
        raise ValueError(f"{plan.pattern_id} formal chain is incomplete or out of order")
    if plan.pattern_id == "pattern-03":
        if len(complete) != 1 or "build_pattern4_independent_display_complete_model" not in complete[0].entrypoint:
            raise ValueError("pattern-03 requires the former Pattern 4 hard-gated complete-model entrypoint")


def validate_execution_paths(snapshot_root: Path, output_dir: Path) -> None:
    snapshot = snapshot_root.resolve()
    output = output_dir.resolve()
    if output == snapshot or output.is_relative_to(snapshot):
        raise ValueError("generation output must remain outside the archive snapshot")
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if not output.is_relative_to(temporary_root):
        raise ValueError("generation output must remain under the system temporary directory")


def validate_final_escapement_envelope(
    step_path: Path,
    expected_envelope: dict[str, list[float]],
    *,
    expected_external_occurrences: tuple[str, ...],
    expected_final_occurrences: tuple[str, ...] | dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Validate the exact external inventory and every final STEP leaf envelope."""

    if step_path.suffix.lower() not in {".step", ".stp"}:
        raise CaptureFailure("final external escapement envelope requires STEP input", path=step_path.name)
    if not step_path.is_file():
        raise CaptureFailure("final STEP is missing", path=step_path.name)

    import glob
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

    root = bd.import_step(step_path)
    violations: list[dict[str, Any]] = []
    external_occurrences: list[str] = []
    expected_final_counts = (
        Counter(expected_final_occurrences)
        if not isinstance(expected_final_occurrences, dict)
        else Counter(expected_final_occurrences)
    )
    expected_final = set(expected_final_counts)

    def inspect(node: Any) -> None:
        children = list(getattr(node, "children", None) or [])
        occurrence = str(getattr(node, "label", ""))
        if occurrence.startswith("external_"):
            external_occurrences.append(occurrence)
        is_unexpected_named_occurrence = (
            bool(expected_final)
            and occurrence not in expected_final
            and occurrence not in {"", "COMPOUND", "SOLID"}
        )
        if occurrence.startswith("external_") or is_unexpected_named_occurrence:
            box = node.bounding_box()
            bounds = {
                "x": [box.min.X, box.max.X],
                "y": [box.min.Y, box.max.Y],
                "z": [box.min.Z, box.max.Z],
            }
            outside_axes = [
                axis
                for axis, (minimum, maximum) in bounds.items()
                if minimum < expected_envelope[axis][0] or maximum > expected_envelope[axis][1]
            ]
            if outside_axes:
                violations.append({
                    "kind": "leaf_outside_final_envelope",
                    "occurrence": occurrence,
                    "bounds": bounds,
                    "outside_axes": outside_axes,
                })
        for child in children:
            inspect(child)

    inspect(root)
    expected_counts = Counter(expected_external_occurrences)
    observed_counts = Counter(external_occurrences)
    for occurrence in sorted(expected_counts.keys() | observed_counts.keys()):
        expected_count = expected_counts[occurrence]
        observed_count = observed_counts[occurrence]
        if observed_count == 0:
            violations.append({
                "kind": "missing_external_occurrence",
                "occurrence": occurrence,
                "expected_count": expected_count,
                "observed_count": observed_count,
            })
        elif expected_count == 0:
            violations.append({
                "kind": "unexpected_external_occurrence",
                "occurrence": occurrence,
                "expected_count": expected_count,
                "observed_count": observed_count,
            })
        elif observed_count != expected_count:
            violations.append({
                "kind": "duplicate_external_occurrence",
                "occurrence": occurrence,
                "expected_count": expected_count,
                "observed_count": observed_count,
            })
    if expected_final_occurrences is not None:
        step_text = step_path.read_text(encoding="utf-8", errors="replace")
        observed_final_counts = Counter(
            match.group(1).replace("''", "'")
            for match in PRODUCT_PATTERN.finditer(step_text)
            if match.group(1)
        )
        for occurrence in sorted(expected_final_counts.keys() | observed_final_counts.keys()):
            expected_count = expected_final_counts[occurrence]
            observed_count = observed_final_counts[occurrence]
            if observed_count == 0:
                kind = "missing_final_occurrence"
            elif expected_count == 0:
                kind = "unexpected_final_occurrence"
            elif observed_count != expected_count:
                kind = "duplicate_final_occurrence"
            else:
                continue
            violations.append({
                "kind": kind,
                "occurrence": occurrence,
                "expected_count": expected_count,
                "observed_count": observed_count,
            })
    return violations


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_final_step_identity(result: dict[str, Any], output_dir: Path) -> str:
    """Bind the final path to its source stage and every derived consumer hash."""

    reported_final_step = Path(result.get("final_step", ""))
    if not reported_final_step.is_absolute():
        raise ValueError("final STEP must use a resolved absolute path inside the capture output directory")
    final_step = reported_final_step.resolve()
    output_root = output_dir.resolve()
    if not final_step.is_file() or not final_step.is_relative_to(output_root):
        raise ValueError("final STEP must be an existing artifact inside the capture output directory")
    source_outputs = [
        stage.get("stage_fingerprint", {})
        for stage in result.get("stages", [])
        if stage.get("stage_fingerprint", {}).get("observation_kind") == "source_design"
        and stage.get("stage_fingerprint", {}).get("output_step_name")
    ]
    if not source_outputs:
        raise ValueError("final STEP path does not match the final source-stage STEP")
    final_hash = _file_sha256(final_step)
    source_fingerprint = source_outputs[-1]
    source_path_value = source_fingerprint.get("output_step_path")
    if not isinstance(source_path_value, str) or not Path(source_path_value).is_absolute():
        raise ValueError("final source-stage STEP must record a resolved absolute path")
    source_path = Path(source_path_value).resolve()
    if not source_path.is_relative_to(output_root) or source_path != final_step:
        raise ValueError("final STEP path does not match the final source-stage STEP")
    if source_fingerprint.get("output_step_sha256") != final_hash:
        raise ValueError("final source-stage STEP hash does not match the captured artifact")
    for stage in result.get("stages", []):
        fingerprint = stage.get("stage_fingerprint", {})
        if fingerprint.get("observation_kind") != "artifact_lineage":
            continue
        input_path_value = fingerprint.get("input_artifact_path")
        if not isinstance(input_path_value, str) or not Path(input_path_value).is_absolute():
            raise ValueError("derived stage input must record the final STEP absolute path")
        input_path = Path(input_path_value).resolve()
        if not input_path.is_relative_to(output_root) or input_path != final_step:
            raise ValueError("derived stage input path does not match the final STEP")
        if fingerprint.get("input_sha256") != final_hash:
            raise ValueError("derived stage final STEP hash does not match the captured artifact")
    return final_hash


def assert_matching_fingerprints(
    fingerprints: list[dict[str, Any]],
    *,
    requested_seed: int,
) -> None:
    if not fingerprints:
        raise ValueError("no source design fingerprints were captured")
    required = {
        "observation_kind", "stage_name", "requested_seed", "resolved_seed", "pattern_id",
        "source_pattern_id", "candidate_id", "axes", "gears", "design_digest",
        "bridge_layout_id", "output_step_name", "unavailable_reasons",
    }
    for fingerprint in fingerprints:
        missing = required - set(fingerprint)
        if missing:
            raise ValueError(f"design fingerprint is missing observed fields: {sorted(missing)}")
        if fingerprint["observation_kind"] != "source_design":
            raise ValueError("source design comparison received a derived artifact fingerprint")
        if fingerprint["requested_seed"] != requested_seed:
            raise ValueError("stage fingerprint requested seed differs from the capture request")
        if fingerprint["resolved_seed"] != requested_seed:
            raise ValueError(
                f"requested seed {requested_seed} resolved as {fingerprint['resolved_seed']} "
                f"in stage {fingerprint['stage_name']}"
            )
        for field in ("pattern_id", "source_pattern_id", "candidate_id", "axes", "gears", "design_digest"):
            if fingerprint[field] is None:
                raise ValueError(f"source design fingerprint has no observed {field}")

    first = fingerprints[0]
    for fingerprint in fingerprints[1:]:
        for field in ("pattern_id", "source_pattern_id", "candidate_id", "design_digest"):
            if fingerprint[field] != first[field]:
                raise ValueError(f"design fingerprint {field} diverged between formal source stages")


def validate_orchestration_result(
    plan: PatternPlan,
    result: dict[str, Any],
    *,
    requested_seed: int,
) -> None:
    stages = result.get("stages")
    if not isinstance(stages, list):
        raise ValueError("formal source chain returned an incomplete stage result")
    planned_prefix = list(plan.stages[:len(stages)])
    if [stage.get("name") for stage in stages] != [stage.name for stage in planned_prefix]:
        raise ValueError("formal source chain returned stages out of order")
    for planned, observed in zip(planned_prefix, stages, strict=True):
        if observed.get("status") != "pass":
            stage_kind = "source-native" if planned.classification == SOURCE_NATIVE else "derived"
            raise ValueError(f"required {stage_kind} stage failed: {planned.name}")
    if len(stages) != len(plan.stages):
        raise ValueError("formal source chain returned an incomplete stage result")
    source_fingerprints = [
        observed["stage_fingerprint"]
        for planned, observed in zip(plan.stages, stages, strict=True)
        if planned.classification == SOURCE_NATIVE
    ]
    assert_matching_fingerprints(source_fingerprints, requested_seed=requested_seed)
    for planned, observed in zip(plan.stages, stages, strict=True):
        if planned.classification != DERIVED:
            continue
        fingerprint = observed.get("stage_fingerprint", {})
        if fingerprint.get("observation_kind") != "artifact_lineage":
            raise ValueError(f"derived stage lacks artifact-lineage observation: {planned.name}")
        unavailable = fingerprint.get("unavailable_reasons", {})
        for field in ("resolved_seed", "candidate_id", "axes", "gears", "design_digest"):
            if fingerprint.get(field) is not None or not unavailable.get(field):
                raise ValueError(f"derived stage must record null+reason for {field}: {planned.name}")


def run_formal_chain(
    snapshot_root: Path,
    output_dir: Path,
    pattern_id: str,
    seed: int,
    reference_python: Path,
) -> dict[str, Any]:
    plan = PATTERNS[pattern_id]
    validate_formal_chain(plan)
    validate_execution_paths(snapshot_root, output_dir)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(snapshot_root), environment.get("PYTHONPATH")) if value
    )
    completed = subprocess.run(
        [str(reference_python), "-c", _DRIVER, str(output_dir), pattern_id, str(seed)],
        cwd=snapshot_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"formal source chain failed:\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(RESULT_MARKER):
            result = json.loads(line.removeprefix(RESULT_MARKER))
            validate_orchestration_result(plan, result, requested_seed=seed)
            result["final_step_sha256"] = validate_final_step_identity(result, output_dir)
            expected_envelope = FINAL_ESCAPEMENT_ENVELOPES.get(pattern_id)
            expected_inventory = FINAL_EXTERNAL_OCCURRENCE_INVENTORIES.get(pattern_id)
            expected_final_inventory = FINAL_OCCURRENCE_COUNT_INVENTORIES.get(pattern_id)
            violations = (
                validate_final_escapement_envelope(
                    Path(result["final_step"]),
                    expected_envelope,
                    expected_external_occurrences=expected_inventory,
                    expected_final_occurrences=expected_final_inventory,
                )
                if expected_envelope is not None and expected_inventory is not None
                else []
            )
            result["expected_final_envelope"] = expected_envelope
            result["expected_external_occurrences"] = list(expected_inventory or ())
            result["expected_final_occurrences"] = list(expected_final_inventory or ())
            result["expected_final_occurrence_counts"] = dict(expected_final_inventory or {})
            result["final_external_envelope_violations"] = violations
            if violations:
                raise CaptureFailure(
                    "final external escapement envelope violation",
                    violations=violations,
                )
            return result
    raise RuntimeError("formal source chain returned without a structured result")


_DRIVER = r'''
import glob
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTCollection, TTFont, TTLibError

old_glob = glob.glob
def safe_glob(pattern, *args, **kwargs):
    values = old_glob(pattern, *args, **kwargs)
    if not str(pattern).lower().endswith(("ttf", "otf", "ttc")):
        return values
    keep = []
    for value in values:
        try:
            font = TTCollection(value) if Path(value).suffix.lower() == ".ttc" else TTFont(value)
            close = getattr(font, "close", None)
            if close:
                close()
            keep.append(value)
        except (OSError, TTLibError):
            pass
    return keep
glob.glob = safe_glob

from models.watch_kinematic.watch_kinematic import partitioned_bridge_stage as bridges
from models.watch_kinematic.watch_kinematic import power_chain_mvp as power
from models.watch_kinematic.watch_kinematic.pattern_card_checklist import write_pattern2_checklist_artifacts
from models.watch_kinematic.watch_kinematic.pattern_cards.separate_hour_minute_no_seconds import PATTERN_CARD_ID as P2_CARD

out = Path(sys.argv[1])
pattern = sys.argv[2]
seed = int(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
captured_designs = []

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def canonical_sha256(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def capture_builder(name):
    original = getattr(power, name)
    def wrapped(*args, **kwargs):
        design = original(*args, **kwargs)
        captured_designs.append((name, design))
        return design
    setattr(power, name, wrapped)

for builder in ("_build_design", "_build_separate_display_design", "_build_independent_display_design"):
    capture_builder(builder)

def primitive(value):
    return isinstance(value, (str, int, float, bool)) or value is None

def deduplicated_gears(value):
    found = {}
    fields = ("gear_id", "axis_id", "teeth", "tooth_count", "module", "module_mm", "pitch_radius", "pitch_radius_mm", "outer_radius", "outer_radius_mm")
    def walk(node):
        if isinstance(node, dict):
            gear_id = node.get("gear_id")
            has_teeth = "teeth" in node or "tooth_count" in node
            has_geometry = any(key in node for key in ("module", "module_mm", "pitch_radius", "pitch_radius_mm", "outer_radius", "outer_radius_mm"))
            if isinstance(gear_id, str) and has_teeth and has_geometry:
                projected = {key: node[key] for key in fields if key in node and primitive(node[key])}
                current = found.setdefault(gear_id, {"gear_id": gear_id})
                for key, candidate in projected.items():
                    if key in current and current[key] != candidate:
                        raise RuntimeError(f"conflicting observed gear field {gear_id}.{key}")
                    current[key] = candidate
            for key, child in node.items():
                if key == "pattern_solver":
                    continue
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
    walk(value)
    return [found[key] for key in sorted(found)]

def fingerprint(stage_name, design, result, output_step_path=None):
    solver = design.get("pattern_solver", {}) if isinstance(design, dict) else {}
    candidate = solver.get("selected_candidate", {}) if isinstance(solver, dict) else {}
    axes = []
    for axis in design.get("axes", []):
        axes.append({key: axis[key] for key in ("axis_id", "x", "y", "x_mm", "y_mm", "z") if key in axis and primitive(axis[key])})
    axes.sort(key=lambda item: item.get("axis_id", ""))
    gears = deduplicated_gears(design)
    bridge_stage = design.get("bridge_stage", {}) if isinstance(design, dict) else {}
    layout = result.get("layout_id") if isinstance(result, dict) else None
    if layout is None and isinstance(bridge_stage, dict):
        layout = bridge_stage.get("layout_id")
    unavailable = {}
    if layout is None:
        unavailable["bridge_layout_id"] = "stage did not create or emit a bridge layout"
    if output_step_path is None:
        unavailable["output_step_name"] = "stage did not emit a STEP artifact"
        unavailable["output_step_path"] = "stage did not emit a STEP artifact"
        unavailable["output_step_sha256"] = "stage did not emit a STEP artifact"
    declared_source_pattern = {
        "pattern-01": "central_hour_minute_offcenter_seconds",
        "pattern-02": "separate_hour_minute_no_seconds",
        "pattern-03": "pattern4_independent_hour_minute_no_seconds",
    }[pattern]
    source_pattern_id = candidate.get("pattern_card_id") if isinstance(candidate, dict) else None
    source_pattern_id = source_pattern_id or declared_source_pattern
    core = {
        "resolved_seed": design.get("seed"),
        "pattern_id": pattern,
        "source_pattern_id": source_pattern_id,
        "candidate_id": candidate.get("candidate_id") if isinstance(candidate, dict) else None,
        "axes": axes,
        "gears": gears,
    }
    return {
        "observation_kind": "source_design",
        "stage_name": stage_name,
        "requested_seed": seed,
        **core,
        "design_digest": canonical_sha256(core),
        "bridge_layout_id": layout,
        "output_step_name": output_step_path.name if output_step_path is not None else None,
        "output_step_path": str(output_step_path.resolve()) if output_step_path is not None else None,
        "output_step_sha256": sha256(output_step_path) if output_step_path is not None else None,
        "unavailable_reasons": unavailable,
    }

def compact_artifacts(result):
    artifacts = result.get("artifacts", {}) if isinstance(result, dict) else {}
    return {
        key: Path(value).name if isinstance(value, str) else value
        for key, value in artifacts.items()
    }

def source_stage(name, call):
    before = len(captured_designs)
    result = call()
    if len(captured_designs) <= before:
        raise RuntimeError(f"source stage did not expose its design observation: {name}")
    design = captured_designs[-1][1]
    artifacts = compact_artifacts(result)
    artifact_paths = result.get("artifacts", {}) if isinstance(result, dict) else {}
    step_value = artifact_paths.get("step") or artifact_paths.get("alias_step")
    step_path = Path(step_value) if isinstance(step_value, str) else None
    return {
        "name": name,
        "status": result.get("status", "pass") if isinstance(result, dict) else "pass",
        "artifact_filenames": artifacts,
        "stage_fingerprint": fingerprint(name, design, result, step_path),
    }, result

stages = []
if pattern == "pattern-01":
    layout = f"pattern1_seed_{seed}_orchestration_baseline"
    observed, base = source_stage("base_engineering_evidence", lambda: power.run_power_chain_mvp(out, seed=seed))
    stages.append(observed)
    observed, final = source_stage(
        "final_analytic_partitioned_bridge_complete_stage",
        lambda: bridges.build_partitioned_bridge_stage(out, seed=seed, layout_id=layout, include_lightening=True),
    )
    stages.append(observed)
elif pattern == "pattern-02":
    layout = f"separate_seed_{seed}_partitioned_bridges"
    observed, base = source_stage(
        "base_engineering_evidence",
        lambda: power.run_power_chain_mvp(out, seed=seed, pattern_card_id=P2_CARD),
    )
    stages.append(observed)
    observed, final = source_stage(
        "complete_partitioned_bridge_stage",
        lambda: bridges.build_separate_display_partitioned_bridge_stage(out, seed=seed, layout_id=layout, include_lightening=True),
    )
    stages.append(observed)
    observed, checklist = source_stage(
        "bridge_checklist",
        lambda: write_pattern2_checklist_artifacts(out, seed=seed),
    )
    stages.append(observed)
else:
    layout = f"pattern4_independent_seed_{seed}_partitioned_bridges"
    observed, final = source_stage(
        "former_pattern4_hard_gated_complete_entry",
        lambda: bridges.build_pattern4_independent_display_complete_model(out, seed=seed, layout_id=layout, include_lightening=True),
    )
    stages.append(observed)

failed_native = [stage["name"] for stage in stages if stage["status"] != "pass"]
if failed_native:
    print("__WATCH_ORCHESTRATION_RESULT__=" + json.dumps({"stages": stages, "failed_native_stages": failed_native}, ensure_ascii=False))
    raise SystemExit(0)

final_step = Path(final["artifacts"]["step"]).resolve()
native_snapshot = out / "_source_native_json"
native_snapshot.mkdir(exist_ok=True)
native_json_files = []
for source_json in sorted(path for path in out.glob("*.json") if path.is_file()):
    destination = native_snapshot / source_json.name
    shutil.copyfile(source_json, destination)
    native_json_files.append(destination.relative_to(out).as_posix())

converter = "from skills.cad.scripts.step.cli import main; raise SystemExit(main())"
converted = subprocess.run([sys.executable, "-c", converter, str(final_step), "--kind", "assembly"], check=False, capture_output=True, text=True)
if converted.returncode:
    raise RuntimeError("STEP to GLB conversion failed:\n" + converted.stdout + "\n" + converted.stderr)
glb = final_step.with_name("." + final_step.name + ".glb")
if not glb.is_file():
    raise RuntimeError("STEP conversion did not create the required Explorer GLB")

derived_reason = "derived artifact stage does not emit or resolve source design fields"
def derived_fingerprint(stage_name, input_path, output_path):
    unavailable_fields = ("resolved_seed", "candidate_id", "axes", "gears", "design_digest", "bridge_layout_id")
    return {
        "observation_kind": "artifact_lineage",
        "stage_name": stage_name,
        "requested_seed": seed,
        "resolved_seed": None,
        "pattern_id": None,
        "source_pattern_id": None,
        "candidate_id": None,
        "axes": None,
        "gears": None,
        "design_digest": None,
        "bridge_layout_id": None,
        "output_step_name": None,
        "input_artifact": input_path.name,
        "input_artifact_path": str(input_path.resolve()),
        "input_sha256": sha256(input_path),
        "output_artifact": output_path.name,
        "output_sha256": sha256(output_path),
        "unavailable_reasons": {field: derived_reason for field in unavailable_fields},
    }

stages.append({
    "name": "step_to_glb",
    "status": "pass",
    "artifact_filenames": {"glb": glb.name},
    "stage_fingerprint": derived_fingerprint("step_to_glb", final_step, glb),
})

motion = final_step.with_suffix(".motion.json")
step_js = final_step.with_name("." + final_step.name + ".js")
if not bridges.sync_browser_bridge_translucency_artifacts(final_step):
    raise RuntimeError("browser artifact synchronization did not update the final STEP artifacts")
if not motion.is_file() or not step_js.is_file():
    raise RuntimeError("browser artifact synchronization omitted motion JSON or STEP module JS")
stages.append({
    "name": "browser_sync",
    "status": "pass",
    "artifact_filenames": {"motion_json": motion.name, "step_module_js": step_js.name},
    "stage_fingerprint": derived_fingerprint("browser_sync", final_step, motion),
})

print("__WATCH_ORCHESTRATION_RESULT__=" + json.dumps({
    "stages": stages,
    "final_step": str(final_step),
    "glb": str(glb),
    "native_json_files": native_json_files,
    "postprocessed_artifacts": {motion.name: "browser_sync", step_js.name: "browser_sync"},
}, ensure_ascii=False))
'''
