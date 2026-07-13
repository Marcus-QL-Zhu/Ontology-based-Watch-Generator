# Task 2 Report: Certified Source Baselines

## Status

Complete. Pattern 1, Pattern 2, and Pattern 3 were recaptured from frozen source commit `5be7852844a3f4c5698a737eba81c026e96ced16`, using an archive snapshot and a fresh operating-system temporary output directory for every run.

The source worktree was not modified. Each baseline records `source.worktree_unchanged: true` and `source.execution_boundary: git archive snapshot only`.

## Pattern 3 Evidence Completion

The former source Pattern 4 complete entrypoint now writes its same-run solver, semantic, role-contract, and kinematic payloads into its complete report. The semantic payload is bound to the Pattern 4 entrypoint identity; this removes the stale identity check inherited from the reused independent-display helper. Geometry, export behavior, and hard-gate behavior are unchanged.

The capture tool extracts these four payloads losslessly from the complete report, retains their JSON pointer and provenance, and rejects a missing, malformed, conflicting, or seed-mismatched payload.

## Captured Baselines

| Public pattern | Source entrypoint | Seed | Result |
| --- | --- | --- | --- |
| Pattern 1 | `central_hour_minute_offcenter_seconds` | 731 | pass |
| Pattern 2 | `separate_hour_minute_no_seconds` | 8459 | pass |
| Pattern 3 | `pattern4_independent_hour_minute_no_seconds` | 731 | pass |

Every record includes a source STEP artifact, GLB conversion lineage, browser synchronization lineage, stage fingerprints, source-native evidence, STEP occurrence inventory, and top/isometric review screenshots. Pattern 3 contains all four complete-entrypoint evidence payloads with source provenance.

## Verification

```text
python -m pytest tests/parity/test_reference_baselines.py -v
48 passed, 4 warnings
```

The suite verifies the capture contract, seed and source fingerprint identity, lossless Pattern 3 embedded-evidence extraction, source-write protection, artifact lineage, external-assembly inventory, and review screenshot hashes.
