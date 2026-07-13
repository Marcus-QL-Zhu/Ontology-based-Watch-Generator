from __future__ import annotations

from pathlib import Path

import build123d as bd

from ontology_watch_generator.integrations.text_to_cad.explorer_artifacts.transcode import generate_explorer_artifacts


def test_step_transcode_writes_explorer_glb_with_topology(tmp_path: Path) -> None:
    step = tmp_path / "sample.step"
    bd.export_step(bd.Box(10, 8, 2), step)

    artifacts = generate_explorer_artifacts(step)

    glb = tmp_path / ".sample.step" / "model.glb"
    assert artifacts == (glb,)
    assert glb.read_bytes()[:4] == b"glTF"
    assert b"STEP_topology" in glb.read_bytes()
