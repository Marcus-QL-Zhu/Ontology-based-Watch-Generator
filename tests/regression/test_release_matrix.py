from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run_release_matrix.py"
SPEC = importlib.util.spec_from_file_location("run_release_matrix", SCRIPT)
assert SPEC and SPEC.loader
MATRIX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MATRIX)


class FakeRecord:
    def __init__(self, artifact_hashes: dict[str, str]):
        self.artifact_hashes = artifact_hashes


def write_fake_run(output_dir: Path, pattern_id: str, seed: int, *, recorded_hash: str | None = None) -> FakeRecord:
    current = output_dir / "current"
    current.mkdir(parents=True)
    artifact = current / "model.step"
    artifact.write_bytes(f"model-{pattern_id}-{seed}".encode())
    actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact_hash = recorded_hash or actual_hash
    (current / "run-record.json").write_text(
        json.dumps(
            {
                "pattern_id": pattern_id,
                "requested_seed": seed,
                "resolved_seed": seed,
                "source_commit": "frozen-source-commit",
                "backend_entrypoint": "fake.generate",
                "design_id": f"{pattern_id}-{seed}",
                "required_artifacts": ["model.step"],
                "artifact_hashes": {"model.step": artifact_hash},
            }
        ),
        encoding="utf-8",
    )
    return FakeRecord({"model.step": artifact_hash})


def test_seed_matrix_declares_six_unique_seeds_for_each_public_pattern():
    seed_matrix = MATRIX.load_seed_matrix(Path(__file__).resolve().parents[2] / "examples" / "release-seeds.json")
    assert set(seed_matrix) == {"pattern-01", "pattern-02", "pattern-03"}
    assert all(len(seeds) == len(set(seeds)) == 6 for seeds in seed_matrix.values())


def test_release_seeds_do_not_include_controlled_rejection_fixtures():
    root = Path(__file__).resolve().parents[2]
    accepted = MATRIX.load_seed_matrix(root / "examples" / "release-seeds.json")
    rejected = json.loads((root / "examples" / "rejection-seeds.json").read_text(encoding="utf-8"))["patterns"]

    assert set(rejected) == set(accepted)
    for pattern_id in accepted:
        assert set(accepted[pattern_id]).isdisjoint(rejected[pattern_id])


def test_matrix_stops_the_failing_pattern_and_records_reason(tmp_path, monkeypatch):
    calls: list[int] = []

    def first(seed: int, output_dir: Path):
        calls.append(seed)
        if seed == 2:
            raise RuntimeError("hard gate failed")
        return write_fake_run(output_dir, "pattern-01", seed)

    monkeypatch.setattr(MATRIX, "GENERATORS", {"pattern-01": first})
    aggregate = MATRIX.run_matrix(seed_matrix={"pattern-01": [1, 2, 3]}, output_dir=tmp_path / "matrix")

    assert calls == [1, 2]
    assert [result["status"] for result in aggregate["results"]] == ["pass", "fail"]
    saved = json.loads((tmp_path / "matrix" / "release-matrix.json").read_text(encoding="utf-8"))
    assert saved["passed"] is False


def test_matrix_rejects_output_inside_repository():
    try:
        MATRIX.run_matrix(seed_matrix={"pattern-01": []}, output_dir=MATRIX.REPO_ROOT / "artifacts")
    except ValueError as error:
        assert "outside" in str(error)
    else:
        raise AssertionError("repository output must be rejected")


def test_matrix_rejects_fresh_run_with_invalid_published_hash(tmp_path):
    def generator(seed: int, output_dir: Path):
        return write_fake_run(output_dir, "pattern-01", seed, recorded_hash="invalid")

    aggregate = MATRIX.run_matrix(
        seed_matrix={"pattern-01": [731]},
        output_dir=tmp_path / "matrix",
        generators={"pattern-01": generator},
    )

    assert aggregate["passed"] is False
    assert aggregate["results"][0]["status"] == "fail"
    assert "published run verification failed" in aggregate["results"][0]["reason"]


def test_default_main_uses_the_empty_mkdtemp_directory(tmp_path, monkeypatch):
    output = tmp_path / "already-created-empty-directory"
    output.mkdir()

    monkeypatch.setattr(MATRIX.tempfile, "mkdtemp", lambda prefix: str(output))
    monkeypatch.setattr(MATRIX, "load_seed_matrix", lambda path: {"pattern-01": [731]})
    monkeypatch.setattr(
        MATRIX,
        "GENERATORS",
        {"pattern-01": lambda seed, output_dir: write_fake_run(output_dir, "pattern-01", seed)},
    )

    assert MATRIX.main([]) == 0


def test_matrix_resume_reuses_matching_completed_run(tmp_path):
    output = tmp_path / "matrix"
    current = output / "pattern-01" / "731" / "current"
    current.mkdir(parents=True)
    artifact = current / "model.step"
    artifact.write_bytes(b"existing-model")
    artifact_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (current / "run-record.json").write_text(
        json.dumps(
            {
                "pattern_id": "pattern-01",
                "requested_seed": 731,
                "resolved_seed": 731,
                "source_commit": "frozen-source-commit",
                "backend_entrypoint": "fake.generate",
                "design_id": "pattern-01-731",
                "required_artifacts": ["model.step"],
                "artifact_hashes": {"model.step": artifact_hash},
            }
        ),
        encoding="utf-8",
    )

    calls: list[int] = []

    def generator(seed: int, output_dir: Path):
        calls.append(seed)
        return write_fake_run(output_dir, "pattern-01", seed)

    aggregate = MATRIX.run_matrix(
        seed_matrix={"pattern-01": [731]},
        output_dir=output,
        generators={"pattern-01": generator},
        resume=True,
    )

    assert calls == []
    assert aggregate["passed"] is True
    assert aggregate["results"] == [
        {
            "pattern_id": "pattern-01",
            "seed": 731,
            "status": "pass",
            "run_record": str(current / "run-record.json"),
            "artifact_hashes": {"model.step": artifact_hash},
            "resumed": True,
        }
    ]
