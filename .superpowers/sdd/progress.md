# Watch Generator Equivalence Migration Progress

## Reference

- Implementation plan: `docs/superpowers/plans/2026-07-11-equivalence-migration.md`
- Migration specification: `docs/superpowers/specs/watch-generator-equivalence-migration-spec.md`
- Frozen source commit: `5be78528`

## Ledger

| Task | Status | Evidence |
| --- | --- | --- |
| 1. Create clean repository and migration ledger | Complete | Commits f59940d..92dd682; task review clean after two documentation fixes |
| 2. Freeze source baselines before copying code | Complete | P1/P2/P3 recaptured from `5be78528`; all required source evidence is present and all parity tests pass. Pattern 3 is now a full certified-equivalence target. |
| 3. Migrate reference backend byte-for-byte with source map | Complete | 72-file frozen closure copied under `src/ontology_watch_generator/reference_backend/`; integrity verifier and tests pass. |
| 4. Define the single-run artifact envelope | Complete | Commit `1bc6436`; atomic publisher copies declared artifacts only, records hashes, and blocks missing or undeclared semantic/motion sidecars. |
| 5. Port Pattern 1 exact public entrypoint | Not started | - |
| 6. Port Pattern 2 exact public entrypoint | Not started | - |
| 7. Port Pattern 3 from former Pattern 4 complete entrypoint | Not started | - |
| 8. Add release matrix, clean install, and upstream contribution map | Not started | - |
| 9. Whole-project validation and open-source readiness review | Not started | - |

## Task 1 constraints observed

- No generator code, generated artifacts, or third-party assets copied.
- Source worktree remains read-only.
- Public mapping is Pattern 1 -> `central_hour_minute_offcenter_seconds`, Pattern 2 -> `separate_hour_minute_no_seconds`, Pattern 3 -> `pattern4_independent_hour_minute_no_seconds`.
- Legacy source Pattern 3 is excluded from public scope.
