# Task 1 Runtime Lock Independent Review

Date: 2026-07-12

Decision: **CHANGES_REQUESTED**

Highest severity: **HIGH**

## Findings

### HIGH: Materialized LFS provenance is not bound to the frozen commit

`materialize_external_step()` returns immediately when the archived STEP bytes equal the source-worktree STEP bytes (`scripts/capture_reference_baseline.py:134-143`). That early return never reads the LFS pointer from `FROZEN_SOURCE_COMMIT` and never compares the accepted SHA-256 with the frozen pointer OID. The pointer comparison at lines 144-151 only runs when the two files differ.

This is a concrete bypass for the archive-smudge path used by the reported real run. A temporary source asset and snapshot containing the same arbitrary bytes (`not-the-frozen-lfs-object`) were accepted and returned with SHA-256 `ccc6994759e4372cb27acf0f506f253071f900aa5aed0cc40ba11647d8b34841`. The real frozen pointer is `313e49a2c323b84d68c2aa47df92ef0c1368338601df83cc9e320cde751c4eae`, but that value is not an implementation constant and is not obtained from `git show <frozen-commit>:<path>` before the early return. Recording the accepted hash therefore provides provenance information without locking provenance to the frozen source.

The added test only proves that equal smudged bytes are accepted. There is no regression test that rejects an asset whose bytes do not match the frozen LFS OID.

### HIGH: The occurrence gate can be bypassed by labels and does not establish an expected external inventory

The gate imports the supplied STEP and computes a bounding box per imported leaf, so it is materially better than a whole-assembly bbox check (`scripts/reference_orchestration.py:239-267`). However, it silently ignores every leaf whose label does not start with `external_`, and it does not require any expected external labels or occurrence count.

A generated final STEP containing an in-envelope decoy labelled `external_escape_staff` and an out-of-envelope detached leaf labelled `escape_staff_geometry` returned `[]`. A STEP with all external labels absent would also pass. Thus a fake/renamed tag can hide detached geometry, contrary to the requested non-bypassable occurrence gate. The implementation also trusts `result["final_step"]` without proving that the path/hash is the final source-stage STEP named by the stage evidence.

The existing detached-leaf test covers only the cooperative case where the remote leaf already has the expected `external_escape_staff` label. It does not cover missing, renamed, duplicated, or decoy labels.

### HIGH: Seed/report/checklist/run-record consistency is observed but not enforced

`validate_orchestration_result()` enforces requested/resolved seed consistency across source-stage fingerprints (`scripts/reference_orchestration.py:309-332`). It does not compare those values with the native solver/semantic evidence, complete geometry report, bridge checklist, or the final run record.

`build_record()` discovers and archives those evidence files, then only asks whether each evidence kind was captured (`scripts/capture_reference_baseline.py:539-549`). A temporary Pattern 2 evidence set in which solver, semantic, complete report, and checklist all used seed `999` produced `missing_required_evidence == []`; the requested run seed could independently remain `8459`. `pattern_card_id` is likewise not cross-checked. The real run happens to contain seed `8459` in the report and checklist, but correctness is accidental rather than a hard gate.

### MEDIUM: The claimed RED-before-GREEN sequence is not independently evidenced and required failure modes are missing from tests

The entire change, including tests and implementation, exists in one commit (`e42f73a`). The implementation report contains prose summaries of an initial RED and later GREEN, but the review package contains no raw RED output or intermediate test-only revision from which the sequence can be reproduced.

The current suite passes (`23 passed`) and does cover missing source `.venv`, a correctly labelled detached leaf, relative runtime provenance fields, use of the supplied reference interpreter for the archived driver, and a successful smudged-archive case. It does not cover LFS asset mismatch against the frozen pointer, fake/missing external labels, report/checklist seed mismatch, final-STEP path/hash binding, or source mutation during a failing capture. Consequently it does not satisfy the requested coverage set.

### MEDIUM: The source write guard is skipped on capture failures

The implementation has no intentional source-generator writes: execution uses the snapshot as `cwd` and `PYTHONPATH`, generation goes to a disjoint system-temp directory, and this change does not delete external leaves or modify/relax the fixed Pattern 2 envelope. The archived driver is correctly launched with the supplied source `.venv` interpreter (`scripts/reference_orchestration.py:345-367`).

However, the post-run source fingerprint and `assert_source_unchanged()` execute only after the snapshot context exits successfully (`scripts/capture_reference_baseline.py:597-623`). Any exception from provenance probing, generation, final STEP validation, or snapshot cleanup jumps directly to the exception handler and skips the after-fingerprint. Therefore the contract does not verify the no-writeback property on precisely the failure paths called out by the task.

## Overall Conclusion

The runtime invocation itself is correctly locked: the archived driver command starts with `source_worktree/.venv/Scripts/python.exe`, runs with the archive snapshot as `cwd`, and places the snapshot first on `PYTHONPATH`. The retained real-run record reports Python `3.11.9`, build123d `0.10.0`, seed `8459`, the expected materialized asset hash, and no envelope violations. The diff contains no external-leaf deletion or envelope relaxation.

Task 1 is nevertheless not approvable because three hard gates remain bypassable: frozen LFS identity, external occurrence identity, and evidence/run seed consistency. The missing negative tests and failure-path source guard leave those gaps unprotected.

## Repair Re-review

Date: 2026-07-12

Decision: **CHANGES_REQUESTED**

Highest severity: **HIGH**

### HIGH: Renamed detached geometry can still hide behind a duplicated expected final label

The external-name counter is now exact, but the final `PRODUCT` inventory is reduced to a set (`scripts/reference_orchestration.py:381, 442-452`). Duplicate expected final labels are therefore invisible. Envelope inspection also skips a non-external node whenever its label belongs to the expected final set (`scripts/reference_orchestration.py:388-393`).

An adversarial STEP with an in-envelope `external_escape_staff` decoy, one legitimate `foundation_mainplate`, and a detached leaf at x=30 renamed to a second `foundation_mainplate` produced two `foundation_mainplate` `PRODUCT` records and `violations == []`. This preserves the complete expected label set while hiding the remote leaf. The required exact final inventory and renamed/decoy resistance are therefore still bypassable.

### HIGH: Final STEP path identity is only a basename check

`validate_final_step_identity()` requires the selected file to be somewhere below the output root, but compares it with the final source-stage output only by `final_step.name` (`scripts/reference_orchestration.py:467-478`). Derived stages are likewise bound only to that basename and the hash of the already-selected path (`scripts/reference_orchestration.py:479-487`).

A result whose source stage named `final.step` accepted `output/decoy/final.step` instead of `output/source-stage/final.step` when the derived fingerprints used the decoy hash. The validator returned the decoy SHA-256. The repair therefore does not force the exact source-stage path; all hash comparisons can consistently describe the same substituted file.

### HIGH: Conflicting Pattern 2 evidence sidecars can be hidden behind the first matching file

Evidence discovery gathers every suffix match but retains only `valid[0]` (`scripts/capture_reference_baseline.py:334-366`). `validate_evidence_identity()` consequently validates only that selected payload (`scripts/capture_reference_baseline.py:438-466`), not every native evidence payload present in the run snapshot.

With `a.semantic.json` carrying seed `8459` and the correct pattern card, and `z.semantic.json` carrying seed `999` and `wrong-pattern`, discovery selected the first file and identity validation passed. Thus the selected solver/semantic/report/checklist identities are now checked, but the requirement that all Pattern 2 evidence identities be forced remains bypassable by a decoy sidecar.

### Resolved original findings

- **Frozen LFS identity: resolved.** `materialize_external_step()` reads the frozen pointer before the equal-smudged path and enforces both OID and byte size (`scripts/capture_reference_baseline.py:146-179`). The new negative test covers mismatched equal-smudged bytes.
- **Source write guard on failure: resolved.** `source_write_guard()` fingerprints in `finally`, and `main()` wraps runtime resolution, snapshot extraction/cleanup, generation, validation, evidence archival, and screenshots inside it (`scripts/capture_reference_baseline.py:124-133, 672-704`).
- **Requested/resolved seed and selected evidence identity: partially resolved.** Source-stage requested/resolved seeds, the four seed-bearing Pattern 2 payloads, and selected payload pattern IDs are checked, but the conflicting-sidecar bypass above prevents closure of the original HIGH.

### Verification

`python -m pytest -v` passes all 34 tests. The passing suite does not cover duplicate expected final labels, a same-basename STEP in a different output subdirectory, or multiple conflicting sidecars of one evidence kind; each bypass was reproduced independently during this re-review.

## Final resolution

The remaining re-review findings were fixed in subsequent hardening commits `398ed8c`, `4b8912c`, and `e380980`. The final targeted suite passed with 47 tests. This file is retained as a historical review trail; the only open evidence limitation is Pattern 3's missing native source sidecars, recorded separately in `pattern3-source-evidence-decision.md` and governed by the preview-only release boundary in the migration spec.
