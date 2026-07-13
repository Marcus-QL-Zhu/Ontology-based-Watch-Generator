"""Artifact naming checks shared by immutable publication paths."""

from __future__ import annotations

SEMANTIC_ARTIFACT_MARKERS = (
    ".semantic.json",
    ".role_contracts.json",
    ".kinematic.json",
    ".validation.json",
    ".motion.json",
)


def is_semantic_or_motion_artifact(filename: str) -> bool:
    return filename.endswith(SEMANTIC_ARTIFACT_MARKERS)
