# Task 2 Orchestration Baseline Review

## Findings

### HIGH - Pattern 2 将必需基础工程阶段的验证失败错误地提升为通过

- `reference_baselines/pattern_02.json:33308-33326` 明确记录 `base_engineering_evidence` 及其原生返回值均为 `status: fail`，但同一记录最终在 `reference_baselines/pattern_02.json:172505` 标为 `status: pass`。
- `scripts/capture_reference_baseline.py:254-262` 只以“六类证据是否有文件”为成功条件，完全没有把任一正式阶段的失败加入 `missing`。测试还在 `tests/parity/test_reference_baselines.py:64-65` 明确允许前置阶段失败，只要求最后两个派生阶段通过。
- 原 runner 的返回状态就是其工程 `validation["status"]`（冻结 source 的 `models/watch_kinematic/watch_kinematic/power_chain_mvp.py:458-460`），不是无关告警。最终桥板 stage 和 checklist 通过不能覆盖必需的基础工程验证失败。
- **明确判断：这违反 spec 7.1 和 9。** Pattern 2 的基础工程证据阶段是正式链的必需组成部分；固定 seed 基线必须代表已通过正式完整链的验收基线，并保留验证项、失败原因及最终状态。当前记录既接受了该失败，也没有保存失败原因，不能作为通过基线。

### HIGH - 基线没有保存后续 parity 所需的原生证据内容

- `scripts/capture_reference_baseline.py:117-128` 对临时输出只保存文件名、哈希和大小；`scripts/capture_reference_baseline.py:157-185` 的 evidence 也只保存来源文件名，不保存或无损提取 solver、semantic、role、motion、kinematic、validation 内容。
- snapshot 在 `scripts/capture_reference_baseline.py:302-307` 后销毁，生成输出仍位于一次性临时目录；例如 `reference_baselines/pattern_02.json:33311-33319` 保存的是已经失效且含本机用户名的绝对临时路径。Pattern 2 基础验证为何失败已经无法从已提交基线恢复。
- spec 9 要求可比较 occurrence、角色、材质/透明度、轴位/齿轮/桥板/螺钉、运动 target/轴/速比/方向，以及验证检查项、失败原因和状态。当前 P1/P2 的 semantic、role、kinematic、validation 仅有哈希与失效路径，不能执行这些等价比较。巨大的 stage `outputs` 也没有补回基础 sidecar 的内容。

### HIGH - 同源指纹不能阻断所有阶段一致地静默换 seed

- `scripts/reference_orchestration.py:107-118` 只比较各阶段 fingerprint 是否彼此相等，不检查每个 fingerprint 的 `requested_seed == resolved_seed`。
- `scripts/reference_orchestration.py:213-228` 的 requested seed 来自命令行，而 resolved seed 来自 design；若所有阶段都把请求 seed 一致地解析成另一个 seed，比较仍会通过。顶层 `resolved_seed` 又在 `scripts/capture_reference_baseline.py:263-264` 被直接写成请求值，反而掩盖这种情况。
- `bridge_layout_id` 和 `final_step_name` 也不是逐阶段观测值：`scripts/reference_orchestration.py:235-260` 把最终 stage 的 layout/STEP 名注入基础阶段和 checklist 的 fingerprint。因此这两个字段的“相等”是编排器预先制造的，不是跨阶段一致性的证据。
- 现有负例 `tests/parity/test_reference_baselines.py:124-138` 只改变轴坐标，没有覆盖静默 seed 替换、候选替换、字段缺失之外的伪一致情形。

### HIGH - 测试主要验证已提交 JSON 的声明，未覆盖实现报告声明的失败模式

- `tests/parity/test_reference_baselines.py:43-90` 信任 `same_run_directory: true`、`worktree_unchanged: true`、stage 名称和 evidence 状态；它没有执行 archive、编排、source 写保护或 evidence 收集，也不能证明这些布尔值不是手工写入。
- 缺少以下关键负例：请求/实际 seed 不同；正式 source-native stage 返回 fail；缺失原生证据导致 capture 失败；source worktree 被写；输出不在新建系统临时目录；GLB/sync/screenshot 失败；报告里只有同名嵌套 key 却被误认为完整证据；post-sync 工件分类错误。
- 测试实际运行结果为 6 passed，但 Pattern 2 的必需阶段失败仍通过测试，直接证明覆盖与声明不一致。

### MEDIUM - `source_native` / `derived` 分类并不真实，report key 探测也过宽

- `scripts/capture_reference_baseline.py:125-126` 把除 GLB 外的所有输出一律标成 `source_native`。但 `scripts/reference_orchestration.py:276-279` 的 derived `browser_sync` 会重写最终 motion JSON 和 STEP module JS；capture 读取的是重写后的文件，因此这两个最终文件不能再简单声明为“formal source stage 的直接输出”。
- `scripts/capture_reference_baseline.py:140-177` 只要任意 `*report.json` 的任意深度出现同名 key，就声明对应 evidence 已捕获；它不验证该节点的 schema、完整性、design/seed 归属或是否真的是可无损提取的原生证据。这会允许无关摘要或占位字段误过门禁。
- 没有发现从 STEP 反推语义或调用第二 solver；STEP 解析仅用于 PRODUCT occurrence label，符合边界。但分类和 evidence 判定仍需收紧。

### MEDIUM - JSON 体积和本机路径泄露造成明显开源与维护问题

- 三个 JSON 分别约 8.96 MB、5.15 MB、82.53 MB，总计约 96.6 MB；Pattern 3 单文件约 272 万行。该变更增加约 322 万行，不适合作为可审阅、可 diff 的长期基线格式。
- 根因之一是 `scripts/reference_orchestration.py:201-211` 在整个嵌套 design 中递归收集 gear，未去重；实测 fingerprint gear 项数为 P1 18,210、P2 6,335、P3 169,059，并在每个 stage 重复。`scripts/capture_reference_baseline.py:241` 又把完整 stage result 原样嵌入记录。
- 已提交 JSON 含 `C:\Users\wande\AppData\Local\Temp\...` 绝对路径（如 `reference_baselines/pattern_02.json:33311-33319`），暴露个人用户名和机器结构，也使重捕获产生无意义 diff。定向搜索未发现 API key、token 或密码，但当前内容仍不满足干净的开源基线要求。

## Conclusion

**CHANGES_REQUESTED（最高严重级别：HIGH）。**

正式阶段确实由冻结 commit `5f0e9b9...` 的单个 `git archive` snapshot 进程依序运行，并共用一个新建系统临时输出目录；P1/P2/P3 的入口顺序与 spec 7.1 基本一致。source stages 从 snapshot import，输出参数指向临时目录，前后又比较 source HEAD/status，因此没有发现写回原 source worktree 的证据。该写保护对 ignored-file 写入没有直接观测，但现有执行边界已显著降低风险。

Pattern 3 的当前失败是正确、清晰且没有伪造：`reference_baselines/pattern_03.json:70-116` 明确列出缺失的 solver、semantic、role-contracts、kinematic，只保留源生 motion/validation，最终状态为 failed（`:2717318`）；没有 STEP 语义推断或第二 solver 填补。

不过，Pattern 2 的基础工程验证失败被错误提升为成功、基线没有保存 spec 9 所需的可比证据、seed 指纹门禁存在绕过路径，且测试没有覆盖这些关键失败模式。Task 2 因此不能批准。

Verification: `python -m pytest tests/parity/test_reference_baselines.py -v` -> 6 passed；该结果同时暴露了测试会接受 Pattern 2 前置正式阶段失败的问题。

## Repair Re-review

### Findings

#### HIGH - 用 seed `8459` 替换固定基线 `55330`，不符合本次受审 plan/spec

- spec 9 在 `docs/superpowers/specs/watch-generator-equivalence-migration-spec.md:202` 明确固定 Pattern 2 seed 为 `55330`；Task 2 Step 3 在 `docs/superpowers/plans/2026-07-11-equivalence-migration.md:79` 再次要求 `55330`。两处都没有允许实现自行替换固定 seed。
- 修复把 `reference_baselines/pattern_02.json:158-160` 改成 `pattern-02-seed-8459`，并在 `tests/parity/test_reference_baselines.py:20-24` 把测试期望同步改成 `8459`。`docs/architecture/reference-baseline-contract.md:18-21` 以实现文档覆盖了上位 spec，而不是满足它。
- 修复报告对 `55330` 的诊断是可信且重要的：该 seed 的必需基础工程 validation 确实失败，不能再提升为 pass。但合规结果应是把 `55330` 保存为明确失败的正式基线并阻断 Task 2，或先通过正式决策修订 spec/plan；不能在本 Task 内自行换成另一个 seed 后宣告 Pattern 2 通过。

#### HIGH - Pattern 2 保存的是基础 runner motion，不是最终完整 STEP 的源生 motion

- `scripts/capture_reference_baseline.py:230-240` 收集同一 suffix 的所有合法 direct sidecar 后无条件选择排序后的 `valid[0]`。Pattern 2 同时产生基础 `watch_power_chain_mvp.motion.json` 和最终桥板模型 motion；排序会选择前者。
- 已提交记录在 `reference_baselines/pattern_02.json:260` 确认 source evidence 来自 `watch_power_chain_mvp.motion.json`，而最终交付 motion 是 `watch_power_chain_separate_display_with_analytic_partitioned_bridges.motion.json`（同文件 `:132`）。基础 motion 为 81,024 bytes，最终 post-sync motion 为 118,083 bytes；基础 evidence 中没有 bridge material contracts。
- 因此 `spec9_coverage` 对最终模型的材质/透明度与运动 target/axis/ratio/direction 声明并不成立。代码确实在 sync 前快照了最终原生 motion，但 evidence 选择逻辑随后丢弃了它。原“保存 Spec 9 可比源生证据”的 HIGH 尚未完全解决。

#### HIGH - 指纹仍不能阻断桥板/checklist 几何漂移

- `scripts/reference_orchestration.py:403-416` 的 `design_digest` 只覆盖 seed、pattern、candidate、axes 和 gears；没有 bridge 边界、service islands、screws、lightening 或对应几何摘要。
- `scripts/reference_orchestration.py:219-223` 跨 source stage 只比较 pattern/source pattern、candidate 和上述 design digest，不比较有观测值的 `bridge_layout_id`，也没有比较桥板/螺钉几何。
- 当前真实 P2 基线已经显示 final bridge stage 的 layout 为 `separate_seed_8459_partitioned_bridges`（`reference_baselines/pattern_02.json:636`），checklist 为 `checklist_seed_8459`（`:841`），仍被接受。名称不同未必等于几何不同，但当前门禁也无法证明二者几何相同。
- `tests/parity/test_reference_baselines.py:159-170` 所谓 geometry drift 只改变 axis `x_mm`；没有对桥板边界、螺钉、镂空或 checklist 重算结果的漂移负例。原“阻断 seed/candidate/geometry 漂移”的 HIGH 只解决了 seed、candidate、axis/gear 部分。

#### MEDIUM - 测试覆盖显著改善，但仍没有覆盖上述真实选择和几何门禁

- 新测试直接调用 runtime 使用的 `validate_orchestration_result`、`discover_native_evidence`、artifact classifier 和路径策略，已经解决“只检查已提交布尔声明”的大部分问题。
- 但 stage failure 测试使用 `_fake_result`（`tests/parity/test_reference_baselines.py:189-229`）；source write 测试只构造两个摘要值后调用比较函数（`:318-323`），没有验证 `_source_tree_state_sha256` 实际发现 ignored file 变化；也没有包含“多个合法 motion sidecar 时必须选择最终完整模型”或“bridge/checklist 几何漂移必须失败”的测试。
- Fresh verification 为 `python -m pytest tests -v` -> `19 passed`。该结果不能覆盖上述缺口，并且测试目前主动接受了违反 spec 的 seed `8459`。

### Resolved Items

- **Pattern 2 failure promotion：实现层已解决。** `scripts/reference_orchestration.py:226-249` 会拒绝任一 required source-native/derived stage failure；`55330` 不再被表示为 pass。
- **路径、体积与开源性：已解决。** 三个主 JSON 为 39,172 / 50,354 / 34,159 bytes；最大 evidence 447,157 bytes。对全部 committed JSON 的绝对用户/temp 路径及 secret 关键词定向扫描无命中。
- **分类：已解决。** sync 前 source-native JSON 被快照，最终 motion/STEP JS 标为 `derived/postprocessed_by_browser_sync`，GLB/截图也正确标为 derived。
- **Pattern 3：已解决并保持诚实失败。** 只保存源生 motion、validation 和 complete report；solver、semantic、role-contracts、kinematic 仍明确 absent，没有 STEP 语义推断或第二 solver 填补。
- **单 snapshot/run 与 source 只读：未发现回归。** 正式 stage 仍从同一 archive snapshot 进程运行、共用一个系统临时输出目录；source 前后摘要增加了 tracked/untracked/ignored metadata 检查。

### Re-review Conclusion

**CHANGES_REQUESTED（最高严重级别：HIGH）。**

四项原 HIGH 中，Pattern 2 失败提升已修复，测试和证据保存也有实质改善；但固定 seed 被未经授权替换，Pattern 2 保存了错误阶段的 motion evidence，且指纹仍不能阻断桥板/checklist 几何漂移。因此 Task 2 仍不能批准。
