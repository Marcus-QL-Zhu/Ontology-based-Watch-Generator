"""Typed, provenance-first description of one generated watch run."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class RunRecord:
    pattern_id: str
    requested_seed: int
    resolved_seed: int
    source_commit: str
    backend_entrypoint: str
    design_id: str
    required_artifacts: tuple[str, ...]
    artifact_hashes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
