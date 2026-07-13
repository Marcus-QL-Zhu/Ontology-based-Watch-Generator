# Task 2 Orchestration Baseline Repair Report

## Outcome

All HIGH/MEDIUM review findings were addressed in the Task 2 implementation and evidence format. The repair does not modify the frozen source worktree, migration spec, implementation plan, progress file, or source code.

Pattern 1 and Pattern 2 now have compact passing baselines. Pattern 3 remains a compact, truthful failed baseline because the frozen complete source chain does not expose four required native evidence classes.

## Pattern 2 Failure Classification

The frozen commit was executed for Pattern 2 seed `55330` in an archive snapshot. `run_power_chain_mvp` returned `status: fail`. Its native `watch_power_chain_mvp.validation.json` recorded:

- failed checks: `independent_geometry_checks`, `independent_internal_interference_geometry`;
- fact source: `axisymmetric_envelope_interference_math`;
- concrete failure: `escape_wheel` versus `display_relay_pinion`, both classified as gears.

This is not a provisional condition. The later partitioned-bridge stage validates bridge construction, and the checklist recomputes bridge plates, bearing coverage, seams, lightening, screw service pads, and final BREP volume. Neither stage reruns or closes the failed internal-interference check. There is therefore no same-source final evidence that can justify a failure whitelist.

Seed `55330` is rejected and is never represented as pass. The repaired Pattern 2 baseline uses seed `8459`, for which the frozen source provides existing accepted generator/bridge evidence and the repaired real capture observes:

- base engineering validation: pass, no failed checks;
- complete partitioned bridge stage: pass;
- bridge checklist: pass, no failed items;
- STEP-to-GLB: pass;
- browser sync: pass;
- requested/resolved seed: `8459`/`8459` in every source stage;
- selected candidate: `separate_display_seed_8459_candidate_0246` in every source stage.

## Implemented Repairs

1. Every formal source-native and derived stage is `required_pass`; no failed stage can be promoted by later success.
2. Source stages fingerprint only their own observed design. Seed equality is asserted before candidate/design comparison. Missing observations are explicit `null + reason`; final values are not backfilled.
3. Gear fingerprints exclude unselected solver candidates, retain actual geometry fields, and deduplicate by `gear_id`. Main baseline JSON no longer embeds stage results.
4. Native JSON is snapshotted before browser sync. Post-sync motion JSON and STEP-module JS are classified `derived/postprocessed_by_browser_sync`; GLB and screenshots are derived.
5. Native evidence is copied or losslessly extracted under `reference_baselines/source_evidence/<pattern>/`. Paths are repository-relative, hashes are stable, and temporary/user paths are excluded.
6. Evidence discovery uses direct sidecar schemas and exact approved report nodes. Arbitrary recursive same-name keys cannot satisfy a requirement.
7. Source protection now checks HEAD, git status, and a file metadata digest that includes ignored and untracked files. Snapshot/output overlap and non-temporary outputs are rejected.
8. Lightweight fake-stage tests cover seed substitution, missing fields, candidate/geometry drift, source-stage failure, GLB/sync failure, malformed/missing evidence, output policy, source write guard, and classification.

## Captured Evidence

| Pattern | Seed | Baseline status | Main JSON size | Native evidence |
| --- | ---: | --- | ---: | --- |
| Pattern 1 | `731` | pass | 39,172 bytes | solver, semantic, roles, motion, kinematic, validation, complete geometry report |
| Pattern 2 | `8459` | pass | 50,354 bytes | solver, semantic, roles, motion, kinematic, validation, complete geometry report, bridge checklist |
| Pattern 3 | `731` | failed | 34,159 bytes | motion, validation, complete geometry report; four required classes explicitly absent |

No committed source-evidence file exceeds 1 MB. The largest is 447,157 bytes. Solver files are lossless selected-candidate extracts rather than multi-megabyte arrays of unselected candidates.

Evidence locations:

```text
reference_baselines/source_evidence/pattern-01/
reference_baselines/source_evidence/pattern-02/
reference_baselines/source_evidence/pattern-03/
```

Each baseline's `spec9_coverage` points to the occurrence, role, material/transparency, axis/gear/bridge/screw, motion, and validation source fields.

## Commands And Results

The source and viewer paths were supplied through the capture CLI/environment and are intentionally omitted from committed data.

```powershell
# Frozen-source diagnosis of the rejected Pattern 2 seed.
python -c "... run_power_chain_mvp(<temporary-output>, seed=55330, pattern_card_id=PATTERN_CARD_ID) ..."
```

Result: exit 0 from the source function with returned `status: fail`; native validation contained the interference failure described above.

```powershell
python scripts/capture_reference_baseline.py --pattern pattern-01 --seed 731 --output <new-system-temp-dir> --source <frozen-source-worktree> --viewer-dir <viewer-dir>
```

Results: two development attempts failed fast while hardening fingerprint extraction (conflicting recursive gear context; absent Pattern 1 candidate pattern label). No capture hung. After restricting gears to real geometry records and taking the source pattern from the invoked stage declaration, the real capture exited 0 and wrote a passing Pattern 1 baseline.

```powershell
python scripts/capture_reference_baseline.py --pattern pattern-02 --seed 8459 --output <new-system-temp-dir> --source <frozen-source-worktree> --viewer-dir <viewer-dir>
```

Result: two real captures exited 0. The final run refreshed the compact solver extract and wrote a passing Pattern 2 baseline.

```powershell
python scripts/capture_reference_baseline.py --pattern pattern-03 --seed 731 --output <new-system-temp-dir> --source <frozen-source-worktree> --viewer-dir <viewer-dir>
```

Result: exited 1 as required after writing `pattern_03.json` with `status: failed`; missing evidence is exactly `solver`, `semantic`, `role_contracts`, and `kinematic`.

```powershell
python -m pytest tests -v
```

Result: `19 passed`.

Targeted path and size audit:

```powershell
Get-Item reference_baselines/pattern_*.json
Get-ChildItem reference_baselines/source_evidence -Recurse -File
rg -n '([A-Za-z]:[\\/](Users|Temp)|C:\\Users\\wande)' reference_baselines
```

Result: all main JSON files are below 1 MB; all evidence files are below 1 MB; no absolute user/temp path was found in committed baseline or source evidence.

## Visual Self-Check

All six refreshed top/isometric screenshots were opened and inspected before this report. They are current, nonblank, and show the intended watch assemblies. The source STEP families also contain detached/floating occurrences that CAD Explorer includes in scene fitting; these appear above or beside the main assembly and make the watch relatively small in frame. This is a source-native visual/occurrence limitation, not hidden or rewritten by Task 2. The screenshots are retained as audit evidence and are not claimed as a passed human visual gate.

## Residual Limitations

- Pattern 3 cannot pass until the source formal chain exposes solver, semantic, role-contract, and kinematic evidence. Task 2 does not infer these from STEP or invoke a second solver.
- Pattern 2's migration spec still names `55330`; the stricter source evidence proves that seed cannot satisfy the full formal-chain gate. This repair follows the review instruction to replace it with the actual all-gates-pass seed `8459` and records the discrepancy explicitly instead of editing the spec.
- Detached/floating source occurrences remain visible in screenshots and require a source-side geometry/occurrence decision outside this repair scope.
