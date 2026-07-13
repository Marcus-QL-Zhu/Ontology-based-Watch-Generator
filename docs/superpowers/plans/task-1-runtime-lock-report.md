# Task 1 Runtime Lock Review-Fix Report

Date: 2026-07-12

## TDD Record

The original review cases were added before implementation. The focused RED run produced 11 expected failures: equal-smudged LFS mismatch was accepted, and the external inventory, renamed/decoy, final STEP identity, evidence identity, and failure-path source guard gates were absent.

```text
python -m pytest tests/parity/test_reference_baselines.py -k "rejects_equal_smudged or external_inventory or renamed_remote_leaf or final_step_identity or evidence_report_and_checklist_identity or source_write_guard_runs" -v
11 failed
```

The focused GREEN run passed all 13 review and existing envelope/provenance cases. The renamed-leaf test specifically uses an in-envelope decoy carrying the expected `external_escape_staff` label while the real staff is renamed and detached.

```text
python -m pytest tests/parity/test_reference_baselines.py -k "materialized_external_step or detached_external_leaf or external_inventory or renamed_remote_leaf or final_step_identity or evidence_report_and_checklist_identity or source_write_guard_runs" -v
13 passed
```

The Repair Re-review cases were then run against commit `4b8912c` with only the new tests applied. All three bypass reproductions failed as expected: a duplicated expected label hid detached geometry, a same-basename STEP in another run subdirectory was accepted, and conflicting semantic sidecars did not raise.

```text
python -m pytest tests/parity/test_reference_baselines.py -k "duplicate_expected_final_label or same_basename_in_different_run_subdirectory or conflicting_matching_native_sidecars" -v
3 failed
```

An additional RED case proved that a correctly named `final.semantic.json` could hide a conflicting semantic sidecar when final-step preference was applied indiscriminately. The repaired sidecar discovery now rejects conflicting identities while retaining exact final-STEP binding for the legitimately multi-stage motion sidecar.

```text
python -m pytest tests/parity/test_reference_baselines.py -k "conflicting_matching_native_sidecars or final_step_named_sidecar or native_sidecar_bound_to_final_step" -v
3 passed
```

## Implemented Gates

- Frozen LFS provenance is read from `git show 5f0e9b9...:<asset-path>` on every path. SHA-256 and byte size must match before equal archive-smudged bytes are accepted.
- Pattern 2 requires the exact 34 external labels and exact final STEP `PRODUCT` multiset: 327 occurrences across 124 labels. Missing, duplicate, renamed, and decoy occurrences fail. External and unexpected named occurrences are checked against the fixed envelope.
- The final STEP must equal the resolved absolute final source-stage path inside the run directory. Its SHA-256 must match the source-stage fingerprint, every derived consumer, and the baseline run record. Archived fingerprints retain run-relative paths rather than machine-specific absolute paths.
- All Pattern 2 native evidence must match `separate_hour_minute_no_seconds_v1`; solver, semantic, complete report, and checklist seeds must match requested/resolved seed `8459`. Multiple conflicting candidates of one evidence kind are rejected instead of selecting the first; only motion uses exact final-STEP sidecar naming to distinguish the final artifact from the legitimate base-stage motion sidecar.
- The source worktree fingerprint comparison runs in `finally`, including generation, validation, evidence, and screenshot failures.

## True Pattern 2 Capture

The successful capture used `C:/Users/wande/Documents/text-to-cad/.venv/Scripts/python.exe` to execute the frozen archive and wrote generated CAD only under:

```text
C:/Users/wande/AppData/Local/Temp/ontology-watch-task1-p2-8459-final-3ba725b0ab214d38a8e72bb2e94910a3
```

- Capture status: `pass`
- Requested/resolved seed: `8459` / `8459`
- Pattern card: `separate_hour_minute_no_seconds_v1`
- Python/build123d: `3.11.9` / `0.10.0`
- Frozen LFS/materialized STEP SHA-256: `313e49a2c323b84d68c2aa47df92ef0c1368338601df83cc9e320cde751c4eae`
- Final STEP SHA-256: `60767b75e7fc71b402e04c20dd2360f53c8a8003dc1e57a997ac1823da7933f5`
- External inventory: `34/34`; final occurrence inventory: `327/327` across `124/124` labels
- Envelope violations: `[]`
- Source write guard: unchanged

The regenerated top and isometric screenshots were visually checked. They show the current coherent assembly with no remote external escapement geometry.

Final verification:

```text
python -m pytest -v
40 passed

python -m py_compile scripts/reference_orchestration.py scripts/capture_reference_baseline.py tests/parity/test_reference_baselines.py
exit 0

git diff --check
exit 0
```
