# text-to-cad Reference Provenance

## Frozen source

- Source worktree: `C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display`
- Source commit: `5be7852844a3f4c5698a737eba81c026e96ced16`
- Source policy: read-only for this migration. No command in this repository may write to the source worktree.

## Selected source patterns

| New public pattern | Source identifier | Source package path | Complete-model source path |
| --- | --- | --- | --- |
| Pattern 1 | `central_hour_minute_offcenter_seconds` | `models/watch_kinematic/watch_kinematic/pattern_cards/central_hour_minute_offcenter_seconds/` | `models/watch_kinematic/watch_kinematic/current_pattern.py` |
| Pattern 2 | `separate_hour_minute_no_seconds` | `models/watch_kinematic/watch_kinematic/pattern_cards/separate_hour_minute_no_seconds/` | `models/watch_kinematic/watch_kinematic/partitioned_bridge_stage.py` (`build_separate_display_partitioned_bridge_stage`) |
| Pattern 3 | `pattern4_independent_hour_minute_no_seconds` | `models/watch_kinematic/watch_kinematic/pattern_cards/pattern4_independent_hour_minute_no_seconds/` | `models/watch_kinematic/watch_kinematic/partitioned_bridge_stage.py` (`build_pattern4_independent_display_complete_model`) |

The new Pattern 3 is sourced from the former Pattern 4 complete-model entrypoint. The source's former Pattern 3 (`independent_hour_minute_no_seconds`) is excluded from the new repository's public API, documentation, tests, and release matrix.

## Copy policy

Task 1 copies no generator code. In later tasks, every copied source file and non-third-party resource must retain a file-level mapping that records its source-relative path and SHA-256 hash. The copied `reference_backend` must preserve source layout and bytes unless an approved migration patch record explicitly documents a change.

## Required run evidence

Each accepted generation must trace its artifacts to the same frozen design object or reference-backend generation record, including requested and resolved seed, STEP occurrence labels, materials, motion, semantics, role contracts, placements, kinematics, validation, and manifest hashes.
