"""Run the fixed public watch-generator seed matrix outside either repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

GENERATORS = None


def default_generators() -> dict:
    """Delay CAD imports so matrix metadata and unit tests need no CAD runtime."""
    from ontology_watch_generator.patterns.pattern_01_central_display import generate_pattern_01
    from ontology_watch_generator.patterns.pattern_02_separate_serial_display import generate_pattern_02
    from ontology_watch_generator.patterns.pattern_03_independent_display import generate_pattern_03

    return {
        "pattern-01": generate_pattern_01,
        "pattern-02": generate_pattern_02,
        "pattern-03": generate_pattern_03,
    }


def load_seed_matrix(path: Path) -> dict[str, list[int]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    patterns = payload["patterns"]
    if set(patterns) != {"pattern-01", "pattern-02", "pattern-03"}:
        raise ValueError("release seed matrix must declare exactly the three public patterns")
    for pattern_id, seeds in patterns.items():
        if len(seeds) != 6 or len(set(seeds)) != 6 or not all(isinstance(seed, int) for seed in seeds):
            raise ValueError(f"{pattern_id} must declare six unique integer seeds")
    return patterns


def _completed_run(run_dir: Path, pattern_id: str, seed: int) -> dict | None:
    record_path = run_dir / "current" / "run-record.json"
    if not record_path.is_file():
        return None
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if (
        record.get("pattern_id") != pattern_id
        or record.get("requested_seed") != seed
        or record.get("resolved_seed") != seed
        or not record.get("source_commit")
        or not record.get("backend_entrypoint")
        or not record.get("design_id")
    ):
        return None
    required = record.get("required_artifacts", [])
    hashes = record.get("artifact_hashes", {})
    if not required or set(required) != set(hashes):
        return None
    for relative_path in required:
        artifact = run_dir / "current" / relative_path
        if not artifact.is_file():
            return None
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != hashes[relative_path]:
            return None
    return {
        "pattern_id": pattern_id,
        "seed": seed,
        "status": "pass",
        "run_record": str(record_path),
        "artifact_hashes": hashes,
        "resumed": True,
    }


def run_matrix(
    *,
    seed_matrix: dict[str, list[int]],
    output_dir: Path,
    generators: dict | None = None,
    resume: bool = False,
) -> dict:
    output_dir = output_dir.resolve()
    if REPO_ROOT in output_dir.parents or output_dir == REPO_ROOT:
        raise ValueError("release matrix output must be outside the repository")
    if output_dir.exists():
        if not resume and any(output_dir.iterdir()):
            raise FileExistsError(f"release matrix output is not empty: {output_dir}")
    else:
        output_dir.mkdir(parents=True)

    active_generators = generators or GENERATORS or default_generators()
    results: list[dict] = []
    for pattern_id, seeds in seed_matrix.items():
        generator = active_generators[pattern_id]
        for seed in seeds:
            run_dir = output_dir / pattern_id / str(seed)
            if resume:
                completed = _completed_run(run_dir, pattern_id, seed)
                if completed is not None:
                    results.append(completed)
                    continue
            try:
                generator(seed=seed, output_dir=run_dir)
                verified = _completed_run(run_dir, pattern_id, seed)
                if verified is None:
                    raise RuntimeError("published run verification failed")
            except Exception as error:
                results.append({"pattern_id": pattern_id, "seed": seed, "status": "fail", "reason": repr(error)})
                break
            verified.pop("resumed", None)
            results.append(verified)

    aggregate = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "results": results,
        "passed": all(result["status"] == "pass" for result in results)
        and len(results) == sum(len(seeds) for seeds in seed_matrix.values()),
    }
    (output_dir / "release-matrix.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    return aggregate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=REPO_ROOT / "examples" / "release-seeds.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    output = args.output or Path(tempfile.mkdtemp(prefix="ontology-watch-release-matrix-"))
    aggregate = run_matrix(seed_matrix=load_seed_matrix(args.seeds), output_dir=output, resume=args.resume)
    print(json.dumps({"passed": aggregate["passed"], "output": str(output)}, indent=2))
    return 0 if aggregate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
