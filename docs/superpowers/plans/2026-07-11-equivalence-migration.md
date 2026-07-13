# 机械手表生成器等价迁移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` task-by-task. Each task is independently reviewed before the next begins.

**Goal:** 建立可开源的 `Ontology-based Watch Generator` 独立仓库，在不改写已验收逻辑的前提下，等价迁移 Pattern 1、Pattern 2、Pattern 3（原 Pattern 4）完整生成闭环，并保留低摩擦回流 `text-to-cad` 的路径。

**Architecture:** 第一阶段把原项目的手表领域代码作为逐文件可追溯的 `reference_backend` 原样迁入，保持它作为唯一建模、求解、材料、运动和验证真源。新仓库只在外部增加薄 CLI、工件清单、基线对照和来源文件；不得建立第二套 solver 或代理几何。所有后续公共抽象只允许从三个已冻结、通过 parity 的模式反向提炼。

**Tech Stack:** Python 3.11, build123d, OpenCascade, pytest/unittest, STEP AP242, CAD Explorer, JSON sidecars, Git.

## Global Constraints

- 新仓库根目录：`C:/Users/wande/Documents/Ontology-based-Watch-Generator`。
- 原仓库只读：`C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display`。
- 模式映射固定为：Pattern 1 -> `central_hour_minute_offcenter_seconds`；Pattern 2 -> `separate_hour_minute_no_seconds`；Pattern 3 -> `pattern4_independent_hour_minute_no_seconds`。
- 原 Pattern 3 不进入新项目正式 API、文档、测试或发布矩阵。
- 迁移阶段不得以重写、简化、stub、代理几何、静默 seed 替换或放宽 validator 达成通过。
- 每个成功工件必须从同一份冻结设计对象或同一份 reference backend 生成记录派生；任何双真源证据都阻断发布。
- 每次生成至少交付：STEP、GLB、STEP JS、solver、semantic、role contracts、placement manifest、motion、kinematic、validation、pattern manifest、hash manifest。
- 基线捕获按原项目的正式多阶段编排链运行；不得把基础 runner、桥板 builder 或后处理函数中的任一个单独视为完整生成器。
- 允许把同一正式运行内的源生报告无损规范化为公开 sidecar；禁止从 STEP 反推语义、以第二个 solver 补写证据，或拼接设计指纹不一致的阶段输出。
- 第三方 Swiss-lever 资产必须单独放在 `third_party/`，保留原始字节、来源、哈希、许可和分发限制。
- 新仓库领域代码不包含绝对本地路径、端口、用户目录、私钥或 API key；text-to-cad 适配层只承担工具调用和发布。
- 所有试验输出写到系统临时目录，不能写回原仓库。

## Task 1: Create the clean repository and migration ledger

**Files:**
- Create: `C:/Users/wande/Documents/Ontology-based-Watch-Generator/.gitignore`
- Create: `README.md`, `LICENSE`, `NOTICE.md`, `THIRD_PARTY_ASSETS.md`, `pyproject.toml`
- Create: `docs/architecture/migration-boundary.md`
- Create: `docs/provenance/text-to-cad-reference.md`
- Create: `docs/superpowers/specs/watch-generator-equivalence-migration-spec.md`
- Create: `docs/superpowers/plans/2026-07-11-equivalence-migration.md`
- Create: `.superpowers/sdd/progress.md`

**Interfaces:**
- Produces a Git repository with no copied generator code and a stable root for every later task.
- Records the source worktree commit, source paths, selected patterns, output contract, and the rule that source remains read-only.

- [ ] **Step 1: Initialize the repository and baseline directories.**
Create the repository only if the target directory does not exist. Initialize Git with `main`. Create `src/`, `tests/parity/`, `tests/integration/`, `reference_baselines/`, `third_party/`, `LICENSES/`, and the listed documentation directories.

- [ ] **Step 2: Write provenance and ownership documents.**
`docs/provenance/text-to-cad-reference.md` must record the full source worktree path, the exact source commit, the three source Pattern paths, and the policy that copied code retains file-level source mapping. `migration-boundary.md` must say that the migration stage has no independent geometry or solver implementation.

- [ ] **Step 3: Write a minimal package declaration.**
Create `pyproject.toml` with Python `>=3.11`, build123d and pytest dependencies, a package name distinct from `text-to-cad`, and no path dependency on the source worktree.

- [ ] **Step 4: Copy the approved migration spec into repository documentation.**
Copy the current equivalence migration spec verbatim to `docs/superpowers/specs/watch-generator-equivalence-migration-spec.md` and place this implementation plan under `docs/superpowers/plans/`.

- [ ] **Step 5: Verify and commit.**
Run `git status --short`, validate the required paths, and commit only repository scaffolding with `chore: initialize watch generator migration repository`.

## Task 2: Freeze source baselines before copying code

**Files:**
- Create: `scripts/capture_reference_baseline.py`
- Create: `scripts/reference_orchestration.py`
- Create: `reference_baselines/pattern_01.json`
- Create: `reference_baselines/pattern_02.json`
- Create: `reference_baselines/pattern_03.json`
- Create: `tests/parity/test_reference_baselines.py`
- Create: `docs/architecture/reference-baseline-contract.md`

**Interfaces:**
- `capture_reference_baseline.py --pattern <id> --seed <seed> --output <temp-dir>` writes a JSON evidence record without modifying the source worktree.
- `reference_orchestration.py` declares the exact source-native stage chain for each public pattern and runs it in one temporary directory.
- Baseline evidence records source commit, every stage entrypoint, requested/resolved seed, same-design fingerprints, source-native evidence, deterministically derived artifacts, STEP occurrence labels, sidecar schemas, material/motion/role contract coverage, and screenshot filenames.

- [ ] **Step 1: Write failing orchestration-baseline tests.**
Tests require every baseline JSON to contain the exact source commit, ordered source stage entrypoints, a source-native/derived/normalized artifact classification, an artifact list, an occurrence list, same-design fingerprints for every stage, semantic/role/motion/kinematic/validation evidence, and a requested seed equal to resolved seed. Tests must reject a raw bridge builder or a raw base runner presented as a complete model.

- [ ] **Step 2: Implement the formal source-only orchestration command.**
Run each pattern's established complete chain in a temporary `git archive` snapshot and collect all mandatory artifacts and their SHA-256 values. Pattern 1 must join the base engineering runner with its analytic partitioned bridge complete-model stage; Pattern 2 must join the base engineering runner, complete partitioned bridge stage and bridge checklist; Pattern 3 must call the former Pattern 4 complete hard-gated entrypoint. All three then run the existing STEP/GLB conversion and browser artifact synchronization. Inspect STEP labels and copy only JSON evidence plus review screenshots into `reference_baselines/`.

- [ ] **Step 3: Capture fixed accepted seeds.**
Use Pattern 1 seed `731`, Pattern 2 seed `55330`, Pattern 3 seed `731`. Fail if a stage fingerprint diverges, an expected source-native evidence item is absent from both direct outputs and the corresponding complete report, an external asset is unavailable, or any output is written into the source worktree. Do not invent it in the new project.

- [ ] **Step 4: Verify and commit.**
Run `python -m pytest tests/parity/test_reference_baselines.py -v`. Commit baseline tooling, evidence and documentation with `test: freeze watch generator reference baselines`.

## Task 3: Migrate the reference backend byte-for-byte with a source map

**Files:**
- Create: `src/ontology_watch_generator/reference_backend/`
- Create: `src/ontology_watch_generator/reference_backend/SOURCE_MAP.json`
- Create: `src/ontology_watch_generator/reference_backend/__init__.py`
- Create: `scripts/verify_reference_backend.py`
- Create: `tests/integration/test_reference_backend_integrity.py`

**Interfaces:**
- `SOURCE_MAP.json` maps every copied Python file and non-third-party resource to its source-relative path and SHA-256.
- `verify_reference_backend.py` fails if a copied source file differs from the recorded source baseline without an approved migration patch record.
- The copied closure includes all modules named by the frozen orchestration chains, not merely the final bridge builders.

- [ ] **Step 1: Write failing copy-integrity tests.**
Tests assert all required source modules for P1/P2/P4, shared bridges/materials/motion utilities, tests and reference assets are mapped. They reject unmapped copies, missing mapped files and hash mismatches.

- [ ] **Step 2: Copy the dependency closure without semantic edits.**
Copy the complete `models/watch_kinematic/watch_kinematic` dependency closure required by the three selected complete-model entrypoints. Preserve relative module layout beneath `reference_backend/`; do not rename functions, rewrite imports, or remove legacy validation paths.

- [ ] **Step 3: Separate the third-party Swiss-lever asset.**
Copy its exact source bytes to `third_party/grabcad/swiss_lever_watch_escapement/`, record original URL/source archive/hash/license restrictions in `THIRD_PARTY_ASSETS.md`, and configure the copied backend to receive this location through a relative project path.

- [ ] **Step 4: Generate source maps and run integrity tests.**
Run the copy verification and `pytest tests/integration/test_reference_backend_integrity.py -v`.

- [ ] **Step 5: Commit.**
Commit only reference backend, source map, third-party provenance and integrity tests using `feat: import watch reference backend`.

## Task 4: Define the single-run artifact envelope without re-solving

**Files:**
- Create: `src/ontology_watch_generator/core/run_record.py`
- Create: `src/ontology_watch_generator/core/artifacts.py`
- Create: `src/ontology_watch_generator/integrations/text_to_cad/publisher.py`
- Create: `tests/integration/test_artifact_envelope.py`
- Create: `docs/architecture/artifact-envelope.md`

**Interfaces:**
- `RunRecord` contains `pattern_id`, `requested_seed`, `resolved_seed`, `source_commit`, `backend_entrypoint`, `design_id`, and `artifact_hashes`.
- `publish_reference_run(run_record, source_output_dir, destination_dir)` copies every required reference artifact atomically, writes `MANIFEST.json`, and rejects missing or extra semantic/motion artifacts.

- [ ] **Step 1: Write failing artifact-envelope tests.**
Use a fixture directory with all required artifact names. Assert atomic publication produces a manifest covering each file. Assert missing `motion.json`, `role-contracts.json`, `model.step.js`, or a requested/resolved seed mismatch fails.

- [ ] **Step 2: Implement the artifact envelope.**
Use a staging directory in the destination parent, SHA-256 each copied file, write `run-record.json` and `MANIFEST.json`, then atomically replace `current/`. The publisher must not parse or regenerate design geometry.

- [ ] **Step 3: Verify and commit.**
Run `pytest tests/integration/test_artifact_envelope.py -v` and commit `feat: add immutable reference artifact envelope`.

## Task 5: Port Pattern 1 as an exact public entrypoint

**Files:**
- Create: `src/ontology_watch_generator/patterns/pattern_01_central_display.py`
- Create: `src/ontology_watch_generator/cli.py`
- Create: `tests/parity/test_pattern_01_parity.py`
- Create: `tests/integration/test_pattern_01_generation.py`
- Create: `docs/patterns/pattern-01-central-display.md`

**Interfaces:**
- `generate_pattern_01(seed: int, output_dir: Path) -> RunRecord`
- CLI: `ontology-watch generate pattern-01 --seed 731 --output <dir>`.

- [ ] **Step 1: Write failing parity tests.**
Generate P1 in a temporary output directory; compare its artifact-name set, requested/resolved seed, occurrence IDs, role IDs, materials, opacity, motion bindings, validation checks and baseline screenshot metadata with `reference_baselines/pattern_01.json`.

- [ ] **Step 2: Implement an adapter-only entrypoint.**
Call only the imported reference P1 complete-model entrypoint. Capture the backend's actual design/report and pass its exact artifacts into Task 4 publisher. Do not create a second solver, create substitute geometry, alter the seed, or reconstruct sidecars.

- [ ] **Step 3: Verify full P1 behavior.**
Run P1 parity/integration tests, validate output with the project's `validate` command, generate GLB, and use CAD Explorer screenshots for agent self-review.

- [ ] **Step 4: Commit.**
Commit `feat: port Pattern 1 exact generation`.

## Task 6: Port Pattern 2 as an exact public entrypoint

**Files:**
- Create: `src/ontology_watch_generator/patterns/pattern_02_separate_serial_display.py`
- Create: `tests/parity/test_pattern_02_parity.py`
- Create: `tests/integration/test_pattern_02_generation.py`
- Create: `docs/patterns/pattern-02-separate-serial-display.md`

**Interfaces:**
- `generate_pattern_02(seed: int, output_dir: Path) -> RunRecord`.

- [ ] **Step 1: Write failing P2 parity tests.**
Compare every mandatory artifact and occurrence against baseline seed `8459`, including bridge seams, service islands, countersunk screws, lightening windows, material/opacity contracts and animation bindings.

- [ ] **Step 2: Implement the adapter-only entrypoint.**
Delegate to the reference P2 complete bridge/lightening generation path and publish through the immutable artifact envelope.

- [ ] **Step 3: Verify.**
Run P2 tests, generate to temp, inspect top/isometric GLB screenshots and confirm no raw output is written into either repository.

- [ ] **Step 4: Commit.**
Commit `feat: port Pattern 2 exact generation`.

## Task 7: Port Pattern 3 from the former Pattern 4 complete entrypoint

**Files:**
- Create: `src/ontology_watch_generator/patterns/pattern_03_independent_display.py`
- Create: `tests/parity/test_pattern_03_parity.py`
- Create: `tests/integration/test_pattern_03_generation.py`
- Create: `docs/patterns/pattern-03-independent-display.md`

**Interfaces:**
- `generate_pattern_03(seed: int, output_dir: Path) -> RunRecord`.

- [ ] **Step 1: Write failing P3 parity tests.**
Require former Pattern 4 hard gates, including independent hour/minute branches, gear case clearance, bridge service band, lightening, materials, opacity, motion and all artifacts.

- [ ] **Step 2: Implement the adapter-only entrypoint.**
Delegate to `build_pattern4_independent_display_complete_model` from the reference backend, map its public identifier to `pattern-03`, and preserve the source identifier in provenance evidence.

- [ ] **Step 3: Verify.**
Run P3 parity/integration tests and agent visual self-review of top/isometric/motion artifacts.

- [ ] **Step 4: Commit.**
Commit `feat: port Pattern 3 exact generation`.

## Task 8: Add release matrix, clean install and upstream contribution map

**Files:**
- Create: `examples/release-seeds.json`
- Create: `scripts/run_release_matrix.py`
- Create: `tests/regression/test_release_matrix.py`
- Create: `docs/architecture/upstream-contribution-map.md`
- Create: `CONTRIBUTING.md`

**Interfaces:**
- Release matrix runs six fixed seeds per pattern and records pass/fail reason, artifact hashes, required occurrence/material/motion coverage and screenshot index.

- [ ] **Step 1: Write failing release-matrix tests.**
Assert all three public patterns run six seeds, stop on hard-gate failure, preserve requested seed, and produce no output inside the source repository.

- [ ] **Step 2: Implement the matrix and clean-clone commands.**
Run each generation in temporary output, retain failure reports, and write an aggregate manifest. Add a documented clean-install invocation.

- [ ] **Step 3: Document the upstream merge path.**
Map each public pattern, reference backend module, adapter, test and asset policy to the intended `text-to-cad` contribution location. State that no upstream core modification is required.

- [ ] **Step 4: Verify and commit.**
Run unit, parity, regression and clean-install tests. Commit `test: add watch generator release matrix`.

## Task 9: Whole-project validation and open-source readiness review

**Files:**
- Create: `docs/release/0.1.0-acceptance.md`
- Modify: `README.md`, `THIRD_PARTY_ASSETS.md`, `NOTICE.md`

- [ ] **Step 1: Run the full suite and static checks.**
Run all tests, formatting/lint checks, three baseline generations and the 18-seed release matrix.

- [ ] **Step 2: Perform agent visual review.**
For one accepted seed per pattern, inspect top and isometric screenshots plus animation. Verify model load, colors, bridge transparency, screws, non-overlapping gears, and absence of placeholder geometry.

- [ ] **Step 3: Run an independent whole-branch review.**
Review provenance, source map, single-source evidence, no-source-write policy, test gaps and third-party packaging restrictions.

- [ ] **Step 4: Publish acceptance evidence and commit.**
Record exact commands, commits, seeds, hashes, visual review conclusion and residual limitations. Commit `docs: record watch generator acceptance evidence`.

## Pattern 3 Complete-Evidence Amendment (2026-07-12)

The user approved one minimal source-side change to the original Pattern 4 complete entrypoint, finalized as `5be78528`: persist the same-run solver, Pattern 4-bound semantic, role-contract, and kinematic payloads with provenance in the complete report. Geometry, hard gates, exports, and model behavior are unchanged. The source is frozen again at that commit for migration.

Task 2 must be re-run from `5be78528` for every Pattern. Pattern 3 is now a certified full-equivalence target and must meet the same artifact, provenance, and release-matrix rules as Pattern 1 and Pattern 2. No preview-only label or missing-evidence exception is permitted.

## Completion Criteria

The migration is complete only after Tasks 1-9 pass. A model that merely opens in CAD Explorer is insufficient. Every public Pattern must have a passing parity baseline, all required sidecars, truthful seed provenance, occurrence-level material/motion/role evidence, hard validation, visual review and an upstream contribution map.
