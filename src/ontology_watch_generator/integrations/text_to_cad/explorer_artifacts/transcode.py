"""Build browser-side GLB/topology artifacts from an already-generated STEP file."""

from __future__ import annotations

from pathlib import Path

from .glb import export_assembly_glb_from_scene
from .render import part_glb_path
from .step_scene import SelectorProfile, extract_selectors_from_scene, load_step_scene, mesh_step_scene


def generate_explorer_artifacts(step_path: Path) -> tuple[Path, ...]:
    """Create a native Explorer GLB without altering CAD geometry or semantics."""

    scene = load_step_scene(step_path)
    mesh_step_scene(scene, linear_deflection=0.12, angular_deflection=0.2, relative=False)
    selectors = extract_selectors_from_scene(scene, profile=SelectorProfile.ARTIFACT)
    glb = export_assembly_glb_from_scene(
        step_path,
        scene,
        linear_deflection=0.12,
        angular_deflection=0.2,
        selector_bundle=selectors,
        include_selector_topology=True,
    )
    if glb != part_glb_path(step_path) or not glb.is_file():
        raise RuntimeError("Explorer GLB export did not produce the expected artifact")
    return (glb,)
