"""Verify that the copied reference backend matches its approved source map."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_BACKEND = PROJECT_ROOT / "src" / "ontology_watch_generator" / "reference_backend"
SOURCE_MAP_PATH = REFERENCE_BACKEND / "SOURCE_MAP.json"
COPIED_ROOTS = ("watch_kinematic", "tests", "references")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copied_files() -> set[str]:
    return {
        path.relative_to(REFERENCE_BACKEND).as_posix()
        for root_name in COPIED_ROOTS
        for root in (REFERENCE_BACKEND / root_name,)
        if root.is_dir()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    }


def verify() -> int:
    if not SOURCE_MAP_PATH.is_file():
        raise ValueError(f"source map is missing: {SOURCE_MAP_PATH}")

    source_map = json.loads(SOURCE_MAP_PATH.read_text(encoding="utf-8"))
    if source_map.get("frozen_source_commit") != "5be7852844a3f4c5698a737eba81c026e96ced16":
        raise ValueError("source map does not identify the required frozen commit")

    entries = source_map.get("files")
    if not isinstance(entries, list):
        raise ValueError("source map files must be a list")

    destinations: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("source map file entry must be an object")
        destination = entry.get("destination")
        source = entry.get("source")
        source_hash = entry.get("sha256")
        if not all(isinstance(value, str) and value for value in (destination, source, source_hash)):
            raise ValueError("source map entries require destination, source, and sha256")
        if destination in destinations:
            raise ValueError(f"duplicate source map destination: {destination}")
        destinations.add(destination)

        file_path = REFERENCE_BACKEND / destination
        if not file_path.is_relative_to(REFERENCE_BACKEND):
            raise ValueError(f"source map destination escapes reference backend: {destination}")
        if not file_path.is_file():
            raise ValueError(f"mapped file is missing: {destination}")

        actual_hash = _sha256(file_path)
        if actual_hash == source_hash:
            continue
        patch = entry.get("migration_patch")
        if not isinstance(patch, dict) or patch.get("approved") is not True:
            raise ValueError(f"unapproved migration patch: {destination}")
        if patch.get("source_sha256") != source_hash or patch.get("patched_sha256") != actual_hash:
            raise ValueError(f"migration patch hash record does not match: {destination}")

    copied_files = _copied_files()
    if copied_files != destinations:
        unmapped = sorted(copied_files - destinations)
        missing = sorted(destinations - copied_files)
        raise ValueError(f"source map coverage mismatch; unmapped={unmapped}; missing={missing}")

    print(f"reference backend integrity verified: {len(entries)} mapped files")
    return 0


def main() -> int:
    try:
        return verify()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"reference backend integrity failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
