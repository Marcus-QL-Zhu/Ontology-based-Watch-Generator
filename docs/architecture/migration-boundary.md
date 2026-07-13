# Migration Boundary

## Purpose

This repository migrates accepted watch-generator behavior from a frozen `text-to-cad` reference worktree while preserving parity and a low-friction future upstream contribution path.

## Source of truth

For every migrated pattern, the imported `reference_backend` is the only source of geometry creation, solving, materials, opacity, motion, semantics, role contracts, placements, and validation. A successful run must derive every published artifact from the same frozen design object or reference-backend generation record.

## Prohibited during equivalence migration

- No independent geometry implementation.
- No second or simplified solver.
- No stub, proxy, placeholder, or substitute geometry.
- No silent seed replacement, relaxed validator, or omitted required sidecar.
- No generated output written into the source worktree.
- No absolute local paths, ports, user directories, private keys, or API keys in domain code.

## Public pattern scope

| Public ID | Frozen source package | Complete-model entrypoint |
| --- | --- | --- |
| `pattern-01` | `central_hour_minute_offcenter_seconds` | source current-pattern complete model |
| `pattern-02` | `separate_hour_minute_no_seconds` | `build_separate_display_partitioned_bridge_stage` |
| `pattern-03` | `pattern4_independent_hour_minute_no_seconds` | `build_pattern4_independent_display_complete_model` |

The former source Pattern 3 is excluded from the new project's public API, documentation, tests, and release matrix.

## Artifact contract

Release 0.1 preserves each frozen backend's native STEP and evidence filenames.
Every successful run publishes the final STEP, its CAD Explorer GLB and motion
sidecars, every native solver/semantic/role/kinematic/validation artifact
produced by that complete entrypoint, plus `run-record.json` and
`MANIFEST.json`. The manifest hashes every declared CAD and evidence artifact.

A cross-pattern `design-ir.json`, placement manifest, and canonical alias set
require a real semantic normalization layer. They are deliberately deferred;
the 0.1 publisher must not manufacture them by renaming incompatible native
payloads or inferring them back from STEP.

## Source isolation

The source worktree remains read-only. All experiments and generation outputs must use only system temporary directories, never the source checkout or this repository. This repository may contain only migration-plan-required baseline evidence and controlled published artifacts; it must not be used as an experiment output location.
