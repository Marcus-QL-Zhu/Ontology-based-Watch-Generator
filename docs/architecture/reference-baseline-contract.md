# Reference Baseline Contract

## Execution Boundary

Task 2 captures source evidence only from commit `5be7852844a3f4c5698a737eba81c026e96ced16`. The caller supplies `--source`, optional `--runtime-root`, and `--viewer-dir`, or sets `ONTOLOGY_WATCH_SOURCE`, `ONTOLOGY_WATCH_RUNTIME_ROOT`, and `ONTOLOGY_WATCH_VIEWER_DIR`; no user-specific path is stored in code or baseline data.

The capture fingerprints the source worktree before and after execution with HEAD, full untracked status, and a metadata digest covering tracked, untracked, and ignored files. It executes `git archive` for the frozen commit and imports source modules only from that temporary snapshot. It always reads the external escapement LFS pointer with `git show <frozen-commit>:<path>`, even when `git archive` already smudged the file. The materialized source asset's SHA-256 and byte size must match that frozen pointer before the snapshot copy can be accepted or replaced. The generation directory must be newly created under the system temporary root and must be outside the snapshot.

The archived driver defaults to `<source-worktree>/.venv/Scripts/python.exe`. `--runtime-root <root>` or `ONTOLOGY_WATCH_RUNTIME_ROOT` may instead select a separate trusted runtime, but resolution is always exactly `<runtime-root>/.venv/Scripts/python.exe`. A missing selected interpreter is a structured capture failure; capture never falls back to `sys.executable`, PATH Python, the source worktree, or another virtual environment. The provenance probe must report the selected interpreter itself and build123d `0.10.0` before generation begins.

Each run records the source code root as a frozen git archive snapshot and the runtime root as either `source_worktree_default` or `explicit_runtime_root`. It also records the Python and build123d version strings, the snapshot-relative materialized external STEP path, and that STEP's SHA-256. Absolute source and runtime paths are intentionally excluded from committed baseline data.

Only compact baseline JSON, source-native JSON evidence, and screenshots are committed. STEP, GLB, HTML, and STEP-module outputs remain temporary. Their baseline inventory stores logical filenames, hashes, sizes, and classifications, never temporary absolute paths.

## Formal Chains And Stage Policy

Every declared stage has policy `required_pass`; this Task 2 baseline defines no provisional stage.

| Public pattern | Required chain | Captured seed | Result |
| --- | --- | ---: | --- |
| `pattern-01` | base engineering evidence -> analytic bridge/lightening/external escapement assembly -> STEP-to-GLB -> browser sync | `731` | pass |
| `pattern-02` | separate-display engineering evidence -> bridge/lightening assembly -> bridge checklist -> STEP-to-GLB -> browser sync | `8459` | pass |
| `pattern-03` | former Pattern 4 hard-gated complete entry -> STEP-to-GLB -> browser sync | `731` | failed baseline because native evidence is incomplete |

Pattern 2 seed `55330` is not provisional evidence. Its frozen base validation fails `independent_geometry_checks` and `independent_internal_interference_geometry` because `escape_wheel` interferes with `display_relay_pinion`. The final bridge stage and checklist do not rerun or close that interference check, so the failure cannot be whitelisted or promoted. Seed `8459` replaces it as the real baseline because the frozen base validation, final bridge stage, checklist, GLB conversion, and sync all pass for the same observed candidate.

After the formal source stages produce the final Pattern 2 STEP, the capture requires the exact 34-label external occurrence inventory and the exact 124-label final STEP `PRODUCT` inventory. Missing, duplicated, renamed, or decoy occurrences fail the capture. Every expected external occurrence is checked at its imported named occurrence node, including its child geometry, against `x=[-22.0,22.0]`, `y=[-22.0,22.0]`, and `z=[-0.675,5.16]` mm. Any unexpected named occurrence is checked against the same envelope so relabeling detached geometry cannot hide it. A whole-assembly bounding box, raw `SOLID` child labels, or GLB-only check cannot satisfy this gate.

The final STEP path must be inside the run output directory and its filename must equal the last STEP-emitting source-stage fingerprint. Its SHA-256 must equal every derived stage's recorded input hash. The baseline records that same filename and hash; a decoy path or stale hash fails before evidence is archived.

## Stage Fingerprints

Each source-native stage observes its own values. A source fingerprint contains requested and resolved seed, public and source pattern IDs, selected candidate ID, axis positions, deduplicated gear facts, a canonical design digest, and that stage's own bridge layout and STEP name.

The capture first asserts `observed resolved seed == requested seed` for every source stage. It then compares candidate ID and design digest across source stages. Gear facts are selected only from actual gear geometry records, omit the solver's unselected candidates, and are deduplicated by `gear_id`.

No final-stage value is inserted into an earlier stage. A base stage without bridges and a checklist without STEP record `null` plus an `unavailable_reasons` entry. Derived GLB and browser-sync stages cannot observe source seed/candidate/axes/gears, so those fields are also explicit `null + reason`; their fingerprints instead bind input and output artifact hashes.

## Evidence Preservation

Source evidence is committed under `reference_baselines/source_evidence/<pattern>/`. Baselines reference it only with repository-relative paths and SHA-256 values.

For Pattern 2, every captured native evidence payload must identify `separate_hour_minute_no_seconds_v1`. Solver, semantic, complete geometry report, and bridge checklist payloads must also record seed `8459`. These identities are compared with the requested seed and source-stage fingerprints before evidence, screenshots, or a passing baseline can be published.

- Direct semantic, role, motion, kinematic, and validation sidecars are copied byte for byte.
- Solver evidence is a lossless selected top-level-field extract containing the real selected candidate, counts, seed, strategy, and status. Unselected candidate arrays are intentionally omitted.
- Complete reports are lossless selected top-level-field extracts containing status, seed, layout, generation gate, validation, bridge stage, and lightening facts while excluding temporary artifact paths.
- Pattern 2 checklist evidence preserves status, failed items, and every checklist item while excluding temporary artifact paths.
- Report fallback is schema-specific. Only Pattern 3's exact top-level `/validation` node can satisfy validation evidence; a nested key with the same name cannot satisfy any evidence class.

The `spec9_coverage` index identifies the exact evidence for occurrence labels; roles; materials/transparency; axes, gears, bridges and screws; motion target/axis/ratio/direction; and validation checks/reasons/status. Missing native evidence is represented as `status: absent`, `value: null`, and an explicit reason, then fails the pattern.

Pattern 3 therefore remains failed: its source chain provides motion and top-level validation, but no compliant solver, semantic, role-contract, or kinematic evidence. No STEP inference or second solver fills those gaps.

## Artifact Classification

- `source_native`: direct, unmodified source-stage outputs.
- `derived`: STEP-to-GLB output, screenshots, and final motion/STEP-module files after browser sync.
- `normalized`: compact stage fingerprints and the evidence coverage index only.

The driver snapshots source-native JSON before browser synchronization. Since sync rewrites final motion JSON and STEP-module JS, the final temporary copies are classified `derived` with derivation `postprocessed_by_browser_sync`; only the pre-sync JSON copy can be source-native evidence.

## Visual Evidence

Each pattern retains top and isometric CAD Explorer screenshots. The screenshots load the current STEP/GLB/STEP-module family and their hashes are tested. Screenshots remain review evidence rather than a substitute for the final STEP occurrence-envelope gate; a capture with detached external leaves fails before it can be accepted as a reference baseline.

The source fingerprint guard is a `finally` boundary around runtime resolution, archive extraction, generation, validation, evidence archival, and screenshots. It checks the post-run worktree fingerprint after success and after every capture failure; a source mutation supersedes the original failure and is reported as a write-guard violation.
