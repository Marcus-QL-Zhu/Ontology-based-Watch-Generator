# Pattern 2 Capture Runtime and Handoff Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让参考基线捕获在与原项目一致的 CAD 运行环境中生成 Pattern 2，并只将经 seed、STEP 哈希和几何包络校验的最终模型交给 CAD Explorer。

**Architecture:** 捕获器继续从冻结的 `git archive` 快照导入源代码，但由原项目锁定的 `.venv` 解释器启动；运行记录显式登记解释器、`build123d`、外部擒纵 STEP 资产哈希、最终 STEP 路径与哈希。最终 STEP 必须通过外部擒纵机构叶子包络校验，浏览器交接只接受该运行记录中被验证的工件。

**Tech Stack:** Python 3.11, build123d/OpenCascade, pytest, STEP AP242, CAD Explorer.

## Global Constraints

- 不修改 `C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display` 中的源代码或生成工件。
- 基线源代码仍只能由 frozen `git archive` 快照执行；输出只写系统临时目录与新仓库的紧凑证据文件。
- 不允许通过删除外部擒纵机构叶子、替换为占位件或放宽几何边界来使测试通过。
- Pattern 2 最终 STEP 必须是正式桥板完整阶段的输出，且 requested/resolved seed、报告 seed 和运行记录 seed 三者一致。
- 任何外部擒纵机构叶子超出主夹板/表壳允许包络时，捕获和浏览器交接必须失败。

---

### Task 1: Lock the reference CAD runtime and reject detached external leaves

**Files:**
- Modify: `scripts/reference_orchestration.py`
- Modify: `scripts/capture_reference_baseline.py`
- Modify: `tests/parity/test_reference_baselines.py`
- Modify: `docs/architecture/reference-baseline-contract.md`

**Interfaces:**
- `resolve_reference_python(source_worktree: Path) -> Path` returns only `source_worktree/.venv/Scripts/python.exe`; missing interpreter raises a structured capture failure.
- `capture_runtime_provenance(...) -> dict` returns Python version, build123d version and materialized external STEP SHA-256.
- `validate_final_escapement_envelope(step_path: Path, expected_envelope: dict) -> list[dict]` returns no violations only when every external occurrence remains inside the permitted final assembly envelope.

- [ ] **Step 1: Write the failing runtime and geometry tests.**

```python
def test_reference_python_requires_source_venv(tmp_path: Path):
    with pytest.raises(CaptureFailure, match="source .venv"):
        resolve_reference_python(tmp_path)

def test_detached_external_leaf_blocks_final_step():
    violations = validate_final_escapement_envelope(
        detached_external_fixture_step,
        {"x": [-22.0, 22.0], "y": [-22.0, 22.0], "z": [-0.675, 5.16]},
    )
    assert {item["occurrence"] for item in violations} == {"external_escape_staff"}
```

- [ ] **Step 2: Run the targeted tests and verify RED.**

Run `python -m pytest tests/parity/test_reference_baselines.py -k "reference_python_requires_source_venv or detached_external_leaf_blocks_final_step" -v`.

Expected: FAIL because the current capturer uses the host interpreter and has no final external-envelope hard gate.

- [ ] **Step 3: Implement the minimal runtime lock and envelope gate.**

```python
reference_python = resolve_reference_python(source_worktree)
runtime = capture_runtime_provenance(reference_python, snapshot_root, external_step)
final_step = orchestration.final_step
violations = validate_final_escapement_envelope(final_step, orchestration.expected_final_envelope)
if violations:
    raise CaptureFailure("final external escapement envelope violation", violations=violations)
```

Run the archived source driver with `reference_python`, not `sys.executable`. Persist only relative evidence paths, runtime version strings and the external asset hash.

- [ ] **Step 4: Run tests and a real Pattern 2 capture.**

Run the targeted tests and then `python scripts/capture_reference_baseline.py --pattern pattern-02 --seed 8459 --output <new-system-temp-dir> --source <source-worktree> --viewer-dir <viewer-dir>`.

Expected: tests pass, capture exits `0`, runtime provenance identifies the source `.venv`, and final external-envelope violations are empty.

- [ ] **Step 5: Commit.**

Commit `fix: lock reference CAD runtime`.

### Task 2: Bind CAD Explorer handoff to the validated run record

**Files:**
- Create: `scripts/open_verified_reference_model.py`
- Modify: `tests/parity/test_reference_baselines.py`
- Create: `docs/superpowers/plans/pattern2-capture-runtime-handoff-report.md`

**Interfaces:**
- `open_verified_reference_model.py --baseline reference_baselines/pattern_02.json --run-dir <temp-dir>` exits nonzero unless the run record's pattern/seed/final STEP SHA-256/envelope status match the selected baseline; on success prints one Explorer URL generated through the render skill's `dev:ensure` command.

- [ ] **Step 1: Write the failing handoff identity tests.**

```python
def test_handoff_rejects_step_from_another_seed(tmp_path: Path):
    with pytest.raises(HandoffError, match="seed or STEP hash"):
        resolve_verified_step(baseline_8459, run_record_55330)

def test_handoff_rejects_failed_envelope():
    with pytest.raises(HandoffError, match="external envelope"):
        resolve_verified_step(baseline_8459, detached_run_record)
```

- [ ] **Step 2: Run tests and verify RED.**

Run `python -m pytest tests/parity/test_reference_baselines.py -k "handoff_rejects" -v`.

Expected: FAIL because no verified handoff resolver exists.

- [ ] **Step 3: Implement the minimal verified resolver.**

```python
def resolve_verified_step(baseline: dict, run_record: dict) -> Path:
    assert baseline["requested_seed"] == run_record["requested_seed"]
    assert baseline["resolved_seed"] == run_record["resolved_seed"]
    assert run_record["final_envelope"]["status"] == "pass"
    assert sha256(run_record["final_step_path"]) == baseline["final_step_sha256"]
    return Path(run_record["final_step_path"])
```

The capture command writes a compact run record beside the temporary final STEP. The opening command reads only that explicit record and never scans `$TEMP` for a newest folder.

- [ ] **Step 4: Run handoff tests and visual self-check.**

Run `python -m pytest tests/parity/test_reference_baselines.py -k "handoff_rejects or verified_step" -v`.

Expected: PASS.

Run `open_verified_reference_model.py` with the newly captured Pattern 2 `8459` run record. Inspect top and isometric snapshots before presenting the Explorer URL; reject the run if external occurrence bounds exceed the recorded envelope.

- [ ] **Step 5: Commit.**

Commit `fix: verify reference model handoff`.

## Completion Criteria

Pattern 2 `8459` is regenerated using the original source `.venv`; its final STEP contains no detached external escapement leaf; the baseline records runtime and asset provenance; and the opened Explorer URL is cryptographically and semantically tied to that same verified run.
