# Pattern 3 源端证据决策（原 Pattern4 完整入口，seed=731）

> **已于 2026-07-12 被后续实施取代。** 用户已批准本文末建议的最小源端持久化改动。提交 `5be78528` 已让正式 Pattern 4 完整入口把四类同次运行的 payload 和来源信息写入 complete report，并将复用语义报告绑定到 Pattern 4 的入口身份。本文保留为根因审计记录，不再定义预览发布边界。

## 范围与结论

本报告只读审计冻结源工作树：

`C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display`

审计对象是原仓库的 Pattern4 硬门禁完整入口
`build_pattern4_independent_display_complete_model()`；它复用原 Pattern3 的独立时/分支路建模实现。这里的“Pattern3”沿用当前迁移任务的语义，而源代码中完整入口的卡片 ID 是
`pattern4_independent_hour_minute_no_seconds_v1`。

**决策：不能把现有 seed=731 的 Pattern4 完整报告无损提升为完整的 solver、semantic、role-contract 与 kinematic 四类正式证据。**

- `solver`：总报告保留了选中候选的检查结果，但没有候选、坐标、比速证明、候选数量及选择过程，不能无推断地重建完整 solver report。
- `semantic`：总报告保留了验证与部分几何事实，但没有 semantic report 的 `seed_manifest`、完整 layout、实体清单和禁用实体清单，不能无损重建。
- `role-contract`：总报告没有 `roles` 或 `contracts`，不能提取。
- `kinematic`：同目录的正式 `motion.json` 已含可用的运动证据；但它不是“同一份 complete report”中的内嵌数据，且源端没有写出独立的 kinematic report。因此总报告本身也不能无损提取完整 kinematic report。

现有正式输出里只有 motion sidecar 可作为该次 Pattern4 完整交付的直接运动证据；其余三类没有对应的同次正式工件。不得以不同入口的 seed=731 输出，或以检查项的 `pass` 状态，替代缺失的原始证据对象。

## 已检查的 seed=731 完整输出

以下四个 Pattern4 目录均只包含两个 JSON 文件：完整总报告与 motion sidecar。它们的 complete-report 根键、`artifacts` 键和 `validation` 键集合相同。

| 目录 | JSON 工件 | 结论 |
| --- | --- | --- |
| `models/watch_kinematic/outputs/pattern4_seed_731_gate_full/` | `pattern4_independent_display_complete_model_report.json`；`watch_power_chain_pattern4_independent_display_with_analytic_partitioned_bridges.motion.json` | 基准完整交付，`status: pass` |
| `models/watch_kinematic/outputs/pattern4_gate_batch_3d/seed_731/` | 同名两件 | 同一工件形态 |
| `models/watch_kinematic/outputs/pattern4_gate_single_seed_731_after_service_band/` | 同名两件 | 同一工件形态 |
| `models/watch_kinematic/outputs/pattern4_seed_731_lightening_smooth_probe/` | 同名两件 | 同一工件形态 |

四份完整总报告的键严格为：

```text
kind, pattern_card_id, status, seed, layout_id, generation_gate,
artifacts, validation, bridge_stage, lightening_enabled
```

其中 `artifacts` 只含 `step`、`motion_json`、`step_module_js`、`report_json`。没有 `solver_json`、`semantic_json`、`role_contract_json` 或 `kinematic_json`。这也与源端 `_pattern4_hard_gate_report()` 的构造一致：
`models/watch_kinematic/watch_kinematic/partitioned_bridge_stage.py:756-794`。

基准总报告为 `status: "pass"`、`seed: 731`，并声明硬门禁策略
`export_step_only_after_all_hard_validation_checks_pass`；路径：
`models/watch_kinematic/outputs/pattern4_seed_731_gate_full/pattern4_independent_display_complete_model_report.json` 的 JSON Pointer `/generation_gate`、`/validation`、`/artifacts`。

## 证据矩阵

| 证据类别 | 同次 Pattern4 正式输出是否存在 | 总报告中可直接得到的内容 | 能否从同一总报告无损提取完整对象 | 判定 |
| --- | --- | --- | --- | --- |
| Solver | 否 | `/validation/solver_checks` 的 19 个 `pass` 状态；`/validation/checks` 的门禁汇总 | 否 | 仅有结论性检查，缺完整候选和几何/比速证明 |
| Semantic | 否 | `/validation/independent_geometry_checks` 及 `/validation/checks` 的派生验证事实 | 否 | 缺完整语义布局、种子清单、实体/禁用实体清单 |
| Role contract | 否 | 少数嵌入几何事实的 `fact_source` 值，例如 `housing_role_contract` | 否 | 没有 `roles` 或每 occurrence 的 contract 链 |
| Kinematic | 是：`*.motion.json` | 总报告仅有 kinematic-related checks；motion sidecar 另含比速、方向、group、DoF 等 | 否 | 可引用 sidecar 作为正式运动证据，但不能从总报告本身抽取完整 kinematic report |

### Solver

完整入口在 `partitioned_bridge_stage.py:616` 调用 Pattern4
`solve_independent_display_layout(seed=seed)`，并在 `:633` 把完整 solver report 传给
`power_chain_mvp._build_independent_display_design()`。但成功路径在 `:684-695` 只把派生后的
`validation` 交给 `_pattern4_hard_gate_report()`；它没有把 `solver_report` 写入 report 或 sidecar。

源 solver 的完整返回对象本应包括 `candidate_count`、`feasible_candidate_count`、`selected_candidate` 和 `candidates`：
`models/watch_kinematic/watch_kinematic/pattern_cards/pattern4_independent_hour_minute_no_seconds/solver.py:50-119`。其中 candidate 持有轴、齿轮、mesh、分支、比速和几何 proofs。总报告的
`/validation/solver_checks` 仅是 `selected_candidate["checks"]`，其复制来源为
`power_chain_mvp.py:1472-1481`，信息量不足以反演完整对象。

### Semantic

完整入口确实在 `partitioned_bridge_stage.py:677` 计算
`p._build_independent_display_semantic_report(design)`；随后在 `:678` 仅把它作为 validation 的输入。
语义对象定义于 `power_chain_mvp.py:1353-1417`，包含 `seed_manifest`、solver 摘要、完整 layout、display、checks、required/forbidden entities。完整报告不含这些字段，故不能无损恢复。

### Role contract

完整入口从未调用 `_build_independent_display_role_contract_report()`。该对象定义于
`power_chain_mvp.py:1594-1660`，其中的 `contracts` 由
`_independent_display_contract()`（`:1697-1709`）提供 occurrence、role、motion/mount/constraint/feature-attachment/validation contracts。总报告没有对应数组；把 geometry report 中的 `fact_source: "housing_role_contract"` 解释为完整 role contract 会新增推断。

### Kinematic 与 motion

完整入口在 `partitioned_bridge_stage.py:669-676` 构造 `motion`，只在硬门禁通过后于 `:697-706` 写入
`<step-stem>.motion.json` 与 STEP-module JS。基准 motion sidecar 的 JSON `kind` 为
`watch_power_chain_independent_display_motion`，记录：

- `physical_hand_angular_velocity_ratio_to_hour_hand`：minute `12.0`、hour `1.0`；
- `signed_display_hand_angular_velocity_ratio_to_hour_hand`：minute `-12.0`、hour `-1.0`；
- `display_motion_works` 的 1:1、1:12 与 1:12 ratio proof；
- 10 个 `moving_groups`、`dynamic_6dof_intent`、`direction_contract` 与 kinematic checks。

来源是 `power_chain_mvp.py:1904-2060`。因此这是一份可追溯的同次正式运动证据，但不是
`_build_independent_display_kinematic_report()` 的输出；后者定义于 `power_chain_mvp.py:1732-1750`，完整入口没有调用。更重要的是 sidecar 的 `pattern_card_id` 是历史共享 helper 的
`independent_hour_minute_no_seconds_v1`，而外层 complete report 是 Pattern4 ID；现有工件必须保留此 provenance 差异，不能静默改写。

## 不能用来补洞的邻近工件

1. `models/watch_kinematic/outputs/independent_display_seed_731_full_model/`、
   `independent_display_seed_731_service_spans_fix/` 与 `_debug_p3_seed731_full/` 的 bridge-stage report
   也只引用 STEP、motion、JS、report，且与 Pattern4 一样只内嵌 validation/solver checks；不是完整四类证据包。
2. `models/watch_kinematic/outputs/separate_display_seed_731/` 确有
   `.solver.json`、`.semantic.json`、`.role_contracts.json`、`.kinematic.json`，但其 card 是
   `separate_hour_minute_no_seconds_v1`（原 Pattern2），不属于 Pattern4/原 Pattern3 的独立双支路求解。不能作为本次交付的替代证据。
3. `power_chain_mvp._run_independent_display_power_chain_mvp()` 会写出四类 granular 工件
   （`power_chain_mvp.py:476-526`），却不生成 analytical bridge stage；它不是已验收的完整桥板交付路径，不能事后与 Pattern4 STEP 拼接并声称同一次生成。

## 最小源端补齐方案

**推荐下一步：修改官方 Pattern4 完整入口，而不是从旧报告抽取或拼接证据。**

最小且无推断的改动限定在
`models/watch_kinematic/watch_kinematic/partitioned_bridge_stage.py` 的
`build_pattern4_independent_display_complete_model()` 成功路径：

1. 保留已经在内存中的 `solver_report`、`semantic` 与 `motion`。
2. 紧接 `semantic = ...`（当前 `:677`）新增两次纯构造调用：
   `p._build_independent_display_role_contract_report(design)` 和
   `p._build_independent_display_kinematic_report(design)`。
3. 在当前 `_pattern4_hard_gate_report(...)` 返回后、写入最终 report 前，把四个**原样对象**写入
   `report["evidence"]`：`solver`、`semantic`、`role_contracts`、`kinematic`。motion 继续以既有
   `artifacts.motion_json` 引用，不复制也不重算。
4. 给每个被嵌入的共享 helper 对象附上最小 provenance 包装，例如
   `{"source_pattern_card_id": "independent_hour_minute_no_seconds_v1", "payload": ...}`；外层报告仍保持
   Pattern4 ID。这样不会把历史 helper 的 Pattern3 ID 伪装成 Pattern4 ID。
5. 扩展 `test_pattern4_complete_model_generates_only_after_hard_validation_passes`
   （`models/watch_kinematic/tests/test_partitioned_bridge_stage.py:129-147`）以断言四个 payload 的
   `kind`、seed、完整入口 ID/provenance，以及既有无 STEP 的失败门禁测试仍通过（`:171-198`）。

该方案不改变 solver、几何、门禁、STEP、motion 或 bridge 的计算，也不从旧 JSON 推导任何新事实；只是将一次成功 Pattern4 运行时已经使用或可直接生成的源对象，连同明确来源，持久化到**同一份官方 complete report**。它是满足“同一 complete report 可无损取得四类证据”这一目标的最小 source-side change。

若后续消费者强制要求四个独立 JSON 文件，而非一个带 `evidence` 的 complete report，则在同一处将上述四个 payload 额外写为 sidecar，并在 `/artifacts` 增加四条路径即可。这是兼容性扩展，不应先于最小补齐改动。

## 建议的实施前验收条件

- 仅以新的官方 Pattern4 一键运行产生的新 seed=731 目录作为证据基准；旧目录保持历史只读。
- 新 complete report 的 `evidence` 必须为原始 JSON payload 或其零损失包装；不得只保存 `pass/fail` 摘要。
- 报告须明确区分外层 Pattern4 `pattern_card_id` 与共享 helper payload 的 source card ID。
- STEP 仍仅在 `generation_gate.allowed_to_open_or_deliver == true` 时写出；证据补齐不得削弱现有硬门禁。

## 精确引用清单

- 官方完整入口及写入顺序：
  `C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display/models/watch_kinematic/watch_kinematic/partitioned_bridge_stage.py:594-707`。
- 总报告 schema/工件键：同文件 `:756-794`。
- semantic、validation、role contract、kinematic、motion 的定义：
  `models/watch_kinematic/watch_kinematic/power_chain_mvp.py:1353-1481`、`:1594-1709`、`:1732-1750`、`:1904-2060`。
- Pattern4 solver 完整返回对象：
  `models/watch_kinematic/watch_kinematic/pattern_cards/pattern4_independent_hour_minute_no_seconds/solver.py:50-119`。
- 基准正式输出：
  `C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display/models/watch_kinematic/outputs/pattern4_seed_731_gate_full/pattern4_independent_display_complete_model_report.json`；
  `C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display/models/watch_kinematic/outputs/pattern4_seed_731_gate_full/watch_power_chain_pattern4_independent_display_with_analytic_partitioned_bridges.motion.json`。
