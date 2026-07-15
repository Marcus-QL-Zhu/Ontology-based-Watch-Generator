from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

from ontology_watch_generator.core.run_record import RunRecord


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "generate_and_open.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("generate_and_open", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _SequenceRandom:
    def __init__(self, values: list[int]) -> None:
        self._values = iter(values)

    def randint(self, _lower: int, _upper: int) -> int:
        return next(self._values)


def _record(seed: int, artifacts: tuple[str, ...]) -> RunRecord:
    return RunRecord(
        pattern_id="pattern-02",
        requested_seed=seed,
        resolved_seed=seed,
        source_commit="test",
        backend_entrypoint="test.generator",
        design_id=f"design-{seed}",
        required_artifacts=artifacts,
    )


def test_generation_retries_with_a_new_seed_after_a_failed_gate(tmp_path: Path) -> None:
    module = _load_script()
    attempted: list[int] = []

    def generator(seed: int, output_dir: Path) -> RunRecord:
        attempted.append(seed)
        if seed == 10:
            raise RuntimeError("source gate failed")
        return _record(seed, ("model.step", ".model.step/model.glb"))

    record = module.generate_until_feasible(
        generator,
        initial_seed=10,
        output_dir=tmp_path,
        max_attempts=3,
        rng=_SequenceRandom([27]),
    )

    assert attempted == [10, 27]
    assert record.resolved_seed == 27


def test_explorer_receives_the_final_step_instead_of_dashboard(tmp_path: Path) -> None:
    module = _load_script()
    current = tmp_path / "current"
    final_step = current / "watch.step"
    explorer_glb = current / ".watch.step" / "model.glb"
    dashboard = current / "dashboard.html"
    explorer_glb.parent.mkdir(parents=True)
    final_step.write_text("STEP", encoding="ascii")
    explorer_glb.write_bytes(b"GLB")
    dashboard.write_text("dashboard", encoding="utf-8")
    record = _record(
        27,
        ("dashboard.html", "watch.step", ".watch.step/model.glb"),
    )
    calls: list[list[str]] = []

    def runner(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="reused CAD Explorer\nhttp://127.0.0.1:4178/?file=current%2Fwatch.step\n",
            stderr="",
        )

    selected = module.find_final_step(record, tmp_path)
    url = module.start_explorer(
        selected,
        workspace_root=tmp_path,
        viewer_dir=tmp_path / "viewer",
        npm="npm.cmd",
        runner=runner,
    )

    assert selected == final_step
    assert str(final_step) in calls[0]
    assert str(dashboard) not in calls[0]
    assert url == "http://127.0.0.1:4178/?file=current%2Fwatch.step"


def test_current_explorer_glb_is_derived_from_the_published_legacy_artifact(
    tmp_path: Path,
) -> None:
    module = _load_script()
    current = tmp_path / "current"
    final_step = current / "watch.step"
    legacy_glb = current / ".watch.step" / "model.glb"
    final_step.parent.mkdir(parents=True)
    legacy_glb.parent.mkdir()
    final_step.write_text("STEP", encoding="ascii")
    legacy_glb.write_bytes(b"glTF-topology")

    prepared = module.prepare_current_explorer_glb(final_step)

    assert prepared == current / ".watch.step.glb"
    assert prepared.read_bytes() == b"glTF-topology"
