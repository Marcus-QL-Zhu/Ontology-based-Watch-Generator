"""Output path helpers for derived Explorer artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


REPO_ROOT = Path.cwd().resolve()


def explorer_directory_for_step_path(step_path: Path) -> Path:
    return step_path.parent / f".{step_path.name}"


def part_glb_path(step_path: Path) -> Path:
    return explorer_directory_for_step_path(step_path) / "model.glb"


def part_native_glb_path(step_path: Path) -> Path:
    return explorer_directory_for_step_path(step_path) / "native.glb"


def relative_to_repo(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
