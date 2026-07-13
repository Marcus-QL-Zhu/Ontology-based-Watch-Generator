# Upstream Contribution Map

This repository begins as an adapter-and-evidence layer around a frozen, file-mapped `text-to-cad` backend. It deliberately avoids a forked geometry or solver implementation.

| Public repository area | Current location | Natural upstream destination | Merge posture |
| --- | --- | --- | --- |
| Pattern 1 public entrypoint | `patterns/pattern_01_central_display.py` | `models/watch_kinematic/.../central_hour_minute_offcenter_seconds/` | Thin adapter may become an official runnable entrypoint. |
| Pattern 2 public entrypoint | `patterns/pattern_02_separate_serial_display.py` | `models/watch_kinematic/.../separate_hour_minute_no_seconds/` | Thin adapter may become an official runnable entrypoint. |
| Pattern 3 public entrypoint | `patterns/pattern_03_independent_display.py` | Former Pattern 4 complete entrypoint | Public name maps to the existing complete generator. |
| Frozen backend | `reference_backend/` plus `SOURCE_MAP.json` | Existing `models/watch_kinematic/watch_kinematic/` modules | No upstream code copy is proposed; source remains authoritative. |
| Immutable publication envelope | `core/` and `integrations/text_to_cad/` | A reusable `text-to-cad` run-artifact layer | Candidate standalone addition after its contract is agreed. |
| Baseline and parity tests | `reference_baselines/`, `tests/parity/` | Source regression suite | Migrate as reference-output regression tests, retaining provenance. |
| Third-party escapement | `src/ontology_watch_generator/third_party/grabcad/` | Separate attributed asset package | Never silently merge into core; preserve source, hash, modification history, and distribution caveats. |

## Integration principle

The easiest future merge is additive: move the publication envelope and parity contracts upstream, point public commands at the upstream canonical modules, and retire the frozen copy only after upstream produces the same evidence and artifacts. No geometry rewrite is required.
