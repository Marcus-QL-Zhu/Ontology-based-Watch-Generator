from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_metadata_declares_all_direct_third_party_imports() -> None:
    metadata = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = metadata["project"]["dependencies"]

    for package in ("build123d", "matplotlib", "numpy", "scipy"):
        assert any(requirement.startswith(package) for requirement in dependencies)


def test_wheel_contains_reference_map_and_attributed_escapement_asset(tmp_path: Path):
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(tmp_path),
            str(REPO_ROOT),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    wheel = next(tmp_path.glob("ontology_based_watch_generator-*.whl"))

    with ZipFile(wheel) as archive:
        names = set(archive.namelist())

    assert "ontology_watch_generator/reference_backend/SOURCE_MAP.json" in names
    assert (
        "ontology_watch_generator/third_party/grabcad/"
        "swiss_lever_watch_escapement/Escapement Model.STEP"
    ) in names
    assert any(name.endswith("text-to-cad-MIT.txt") for name in names)
