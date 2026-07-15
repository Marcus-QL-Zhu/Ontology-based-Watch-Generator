"""Generate a feasible watch design and hand its final STEP to CAD Explorer."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import re
import secrets
import shutil
import subprocess
import tempfile
from typing import Callable

from ontology_watch_generator.core.run_record import RunRecord


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SEED_MAX = 2_147_483_647
URL_PATTERN = re.compile(r"https?://[^\s]+")
PATTERN_IDS = ("pattern-01", "pattern-02", "pattern-03")


def load_generators() -> dict[str, Callable[[int, Path], RunRecord]]:
    from ontology_watch_generator.cli import GENERATORS

    return GENERATORS


def generate_until_feasible(
    generator: Callable[[int, Path], RunRecord],
    initial_seed: int,
    output_dir: Path,
    max_attempts: int,
    rng: random.Random | None = None,
) -> RunRecord:
    """Retry failed source gates with distinct seeds, preserving each exact attempt."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    random_source = rng or random.Random(initial_seed)
    attempted: list[int] = []
    seed = initial_seed
    last_error: Exception | None = None
    for _attempt in range(max_attempts):
        attempted.append(seed)
        try:
            return generator(seed, output_dir)
        except (RuntimeError, ValueError) as error:
            last_error = error
        while seed in attempted:
            seed = random_source.randint(1, SEED_MAX)
    attempted_text = ", ".join(str(value) for value in attempted)
    raise RuntimeError(
        f"No feasible design after {max_attempts} attempts; seeds: {attempted_text}"
    ) from last_error


def find_final_step(record: RunRecord, output_dir: Path) -> Path:
    """Select the STEP that owns the run's adjacent CAD Explorer GLB artifact."""

    artifacts = {Path(name).as_posix() for name in record.required_artifacts}
    candidates: list[Path] = []
    for name in artifacts:
        relative_step = Path(name)
        if relative_step.suffix.lower() not in {".step", ".stp"}:
            continue
        glb = relative_step.parent / f".{relative_step.name}" / "model.glb"
        if glb.as_posix() in artifacts:
            candidates.append(output_dir / "current" / relative_step)
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected one final STEP with CAD Explorer data, found {len(candidates)}"
        )
    final_step = candidates[0]
    if not final_step.is_file():
        raise RuntimeError(f"Final STEP does not exist: {final_step}")
    return final_step


def prepare_current_explorer_glb(final_step: Path) -> Path:
    """Expose the packaged legacy GLB at the path expected by current Explorer."""

    current_glb = final_step.parent / f".{final_step.name}.glb"
    if current_glb.is_file():
        return current_glb
    packaged_glb = final_step.parent / f".{final_step.name}" / "model.glb"
    if not packaged_glb.is_file():
        raise RuntimeError(f"Packaged CAD Explorer GLB does not exist: {packaged_glb}")
    shutil.copy2(packaged_glb, current_glb)
    return current_glb


def resolve_viewer_dir(explicit: Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    environment_viewer = os.environ.get("ONTOLOGY_WATCH_VIEWER_DIR")
    if environment_viewer:
        candidates.append(Path(environment_viewer))
    text_to_cad_root = os.environ.get("TEXT_TO_CAD_ROOT")
    if text_to_cad_root:
        candidates.append(Path(text_to_cad_root) / ".agents/skills/render/scripts/viewer")
    candidates.extend(
        [
            REPOSITORY_ROOT / ".agents/skills/render/scripts/viewer",
            REPOSITORY_ROOT.parent / "text-to-cad/.agents/skills/render/scripts/viewer",
        ]
    )
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if (resolved / "package.json").is_file():
            return resolved
    raise RuntimeError(
        "CAD Explorer viewer not found; set ONTOLOGY_WATCH_VIEWER_DIR or TEXT_TO_CAD_ROOT"
    )


def start_explorer(
    final_step: Path,
    workspace_root: Path,
    viewer_dir: Path,
    npm: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    npm_command = npm or shutil.which("npm.cmd") or shutil.which("npm")
    if npm_command is None:
        raise RuntimeError("npm is required to start CAD Explorer")
    command = [
        npm_command,
        "--prefix",
        str(viewer_dir),
        "run",
        "dev:ensure",
        "--",
        "--workspace-root",
        str(workspace_root.resolve()),
        "--file",
        str(final_step.resolve()),
    ]
    result = runner(command, check=True, capture_output=True, text=True)
    urls = URL_PATTERN.findall(result.stdout)
    if not urls:
        raise RuntimeError("CAD Explorer started without returning a review URL")
    return urls[-1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate until feasible, then print the CAD Explorer review URL."
    )
    parser.add_argument("pattern", choices=PATTERN_IDS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(tempfile.gettempdir()) / "ontology-watch-generator",
    )
    parser.add_argument("--viewer-dir", type=Path)
    args = parser.parse_args(argv)

    initial_seed = args.seed if args.seed is not None else secrets.randbelow(SEED_MAX) + 1
    generators = load_generators()
    record = generate_until_feasible(
        generators[args.pattern],
        initial_seed=initial_seed,
        output_dir=args.output,
        max_attempts=args.max_attempts,
    )
    final_step = find_final_step(record, args.output)
    prepare_current_explorer_glb(final_step)
    url = start_explorer(
        final_step,
        workspace_root=args.output,
        viewer_dir=resolve_viewer_dir(args.viewer_dir),
    )
    print(json.dumps(record.to_dict(), indent=2))
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
