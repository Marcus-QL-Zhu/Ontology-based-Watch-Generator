# Pattern 2 Source Call-Chain Audit

## 范围与结论

审计对象为只读原仓库 `C:\Users\wande\.config\superpowers\worktrees\text-to-cad\codex-watch-separate-display` 中 Pattern 2：`separate_hour_minute_no_seconds`（卡片 ID：`separate_hour_minute_no_seconds_v1`）。本报告没有改动原仓库。

结论：`build_separate_display_partitioned_bridge_stage()` 是一个**桥板阶段生成函数**，不是 Pattern 2 的完整硬门禁交付入口。它会重新求解布局、生成含完整桥板和镂空的 STEP、motion JSON、STEP-module JS 及 stage report；但它不生成 Pattern 2 的 semantic / role-contract / kinematic / validation / solver JSON，也不在 STEP 导出前以这些报告实施硬门禁。原仓库中不存在一个单独的 Pattern 2 Python 函数能一次性产出所有真实工件。

可复现已验收实物目录中全部工件的最短完整流程是一个编排序列：先运行无桥基础证据包，再运行桥板阶段，再运行独立桥板 checklist，然后由仓库外 CAD Explorer 转换步骤产生 GLB，最后反写浏览器侧透明桥板绑定并截图。该序列可封装成一个一键脚本，但该脚本本身不在原仓库中。

## 已验收输出证据

最新非空的完整 Pattern 2 目录是：

`models\watch_kinematic\outputs\p2_seed_55330_complete_model\`

其中 stage report 记录：`status=pass`、`seed=55330`、`lightening_enabled=true`，并且包含：

- `watch_power_chain_separate_display_with_analytic_partitioned_bridges.step`
- `watch_power_chain_separate_display_with_analytic_partitioned_bridges.motion.json`
- `.watch_power_chain_separate_display_with_analytic_partitioned_bridges.step.js`
- `.watch_power_chain_separate_display_with_analytic_partitioned_bridges.step.glb`
- `render_front_ortho.png`、`render_top_ortho.png`、`render_iso_shaded_edges.png`

时间顺序也支持调用链判断：STEP / motion / JS / report 在 `2026-07-07 23:21:52` 写入，隐藏 GLB 在 `23:22:52` 才出现，三张 render PNG 在 `23:27:29` 出现。因此 GLB 和截图不是 `build_separate_display_partitioned_bridge_stage()` 的 Python 直接输出。

`p2_seed_2791_complete_model` 与若干随机 seed 目录为空；它们不应被当作可复现基准。较早的 `p2_gate_*`、`p2_random_*` 目录可作为同一 stage 入口的历史回归样本。

## Pattern 2 源码入口

卡片 package 的正式入口是：

`models\watch_kinematic\watch_kinematic\pattern_cards\separate_hour_minute_no_seconds\__init__.py`

它导出 `PATTERN_CARD_ID`、`solve_separate_display_layout()`、卡片写入函数及二维 review 写入函数。`separate_display_pattern.py` 仅为兼容 facade；不包含独立实现。

布局求解起点是：

`pattern_cards\separate_hour_minute_no_seconds\solver.py:43` `solve_separate_display_layout()`

它枚举 escape pinion 齿数、输入 relay 角度偏置、显示 relay 分支偏置，构造候选并选择第一个 pass 候选。每个候选由 `_build_separate_display_candidate()` 产生轴、显示齿轮、四个 mesh、比速证明、中心距证明、扫掠与几何检查；`_candidate_checks()` 汇总 Pattern 2 约束。

## 基础无桥证据包调用链

公开入口：`power_chain_mvp.py:362` `run_power_chain_mvp(output_dir, seed=..., pattern_card_id=SEPARATE_DISPLAY_PATTERN_CARD_ID)`。

该函数分派到 `power_chain_mvp.py:422` `_run_separate_display_power_chain_mvp()`，完整链如下：

```text
run_power_chain_mvp
  -> _run_separate_display_power_chain_mvp
     -> solve_separate_display_layout
     -> _build_separate_display_design
     -> _build_separate_display_assembly
        -> build_external_escapement_parts
     -> _build_separate_display_semantic_report
     -> _build_separate_display_motion_report
     -> _build_separate_display_validation_report
        -> _build_independent_geometry_report
        -> _separate_display_task4_checks
     -> _build_separate_display_role_contract_report
     -> _build_separate_display_kinematic_report
     -> build123d.export_step
     -> _render_step_module_js
```

此入口写入以下基础工件（basename 为 `watch_power_chain_mvp`）：

| 工件 | 生产函数 |
| --- | --- |
| `.step` | `_build_separate_display_assembly()` 后的 `export_step()` |
| `.solver.json` | `solve_separate_display_layout()` 的完整 report |
| `.semantic.json` | `_build_separate_display_semantic_report()` |
| `.kinematic.json` | `_build_separate_display_kinematic_report()` |
| `.role_contracts.json` | `_build_separate_display_role_contract_report()` |
| `.validation.json` | `_build_separate_display_validation_report(design, semantic, motion)` |
| `.motion.json` | `_build_separate_display_motion_report()` |
| `.<step-name>.js` | `_render_step_module_js(motion)` |
| `dashboard.html` | `_render_separate_display_dashboard()` |

注意：这个入口完全不启用桥板（design 的 `bridges_generated` 保持 false），所以它是完整的 Pattern 2 语义/运动证据包，但不是已验收目录中的完整桥板实物。

## 桥板、镂空与 STEP 调用链

入口：`partitioned_bridge_stage.py:340` `build_separate_display_partitioned_bridge_stage(output_dir, seed=8459, layout_id=None, include_lightening=False)`。

真实阶段调用链：

```text
build_separate_display_partitioned_bridge_stage
  -> solve_separate_display_layout
  -> power_chain_mvp._build_separate_display_design
  -> build_separate_display_bridge_stage_plan
     -> solve_bridge_xy_partition(... Pattern 2 axis groups / links ...)
     -> separate_display_axis_voronoi_probe._axis_voronoi
     -> separate_display_axis_voronoi_probe._axis_voronoi_seam_plan
     -> _separate_display_continuous_region_footprints
     -> _bridge_record (bridge / bearing clearance / pads / screws)
  -> [include_lightening=True]
     -> bridge_lightening.solve_bridge_lightening_plan
        -> _solve_bridge_lightening (per bridge)
        -> manufacturing_windows + fastener_web_clearance
  -> design["bridges_generated"] = True
  -> design["bridge_stage"] = bridge_stage
  -> power_chain_mvp._build_separate_display_assembly
     -> build_external_escapement_parts
     -> partitioned_bridge_stage._make_analytic_bridge_stage
        -> analytic footprint extrusion
        -> upper-bearing clearance holes
        -> lightening manufacturing-window subtraction
        -> annular support pads, countersinks, bridge screws
  -> _flatten_for_step_color_sync / _leaf_with_synced_review_material
  -> build123d.export_step
  -> power_chain_mvp._build_separate_display_motion_report(feature_refs_override=...)
  -> power_chain_mvp._render_step_module_js
  -> separate_display_partitioned_bridge_stage_report.json
```

关键实现位置：

- `partitioned_bridge_stage.py:243` 的 `build_separate_display_bridge_stage_plan()` 是 Pattern 2 的桥板计划，不使用 grid contour 作为 CAD 边界；它将 grid 定位为 search/feasibility only。
- `partitioned_bridge_stage.py:340` 的 stage builder 仅在 `include_lightening=True` 时向 bridge records 附加 `manufacturing_windows`。
- `partitioned_bridge_stage.py:1873` 的 `_make_analytic_bridge_stage()` 真正将连续桥板 footprint 挤出为 BREP，并在 `1903-1910` 对 manufacturing windows 做减料；因此已验收 STEP 的镂空是实体几何，不只是 JSON 注释。
- `power_chain_mvp.py:1193` 的 `_build_separate_display_assembly()` 在 `bridges_generated` 为真时调用 `_make_analytic_bridge_stage()`；这是完整桥板被装入总装的唯一分支。
- stage builder 以 `feature_refs_override` 传入扁平可见叶节点引用，保证 motion 的 bridge material / selector 面向 STEP 叶实体。

stage builder 仅写入：

```text
watch_power_chain_separate_display_with_analytic_partitioned_bridges.step
watch_power_chain_separate_display_with_analytic_partitioned_bridges.motion.json
.watch_power_chain_separate_display_with_analytic_partitioned_bridges.step.js
separate_display_partitioned_bridge_stage_report.json
```

它没有调用 `_build_separate_display_semantic_report()`、`_build_separate_display_kinematic_report()`、`_build_separate_display_validation_report()` 或 `_build_separate_display_role_contract_report()`；report 的 status 也只取决于 `bridge_stage["status"]`。因此它不是完整模型/硬门禁入口，尽管历史目录名常写作 `full_model` 或 `complete_model`。

## 独立桥板验证与材料/运动

`pattern_card_checklist.py:54` 的 `run_pattern2_bridge_checklist()` 是独立的几何复算 gate：

```text
run_pattern2_bridge_checklist
  -> _build_pattern2_design_and_bridge_stage
     -> solver + design + build_separate_display_bridge_stage_plan
     -> solve_bridge_lightening_plan
     -> _make_analytic_bridge_stage
  -> six checks: required plates, bearing coverage, true seam gap,
     lightening validity, screws-in-service-pads, final BREP volume
```

`write_pattern2_checklist_artifacts()` 只写 `checklist.json` 与 `checklist.html`。它显式忽略 `generate_step` 参数，不导出 STEP，所以也不能代替 stage builder。

Pattern 2 motion material contracts 出自 `power_chain_mvp.py:1753` `_build_separate_display_motion_report()`：它生成 moving groups、fixed features、6DoF intent、feature refs、`semantic_material_contracts` 与 `visual_materials`，随后由 `_render_step_module_js()` 写 sidecar。桥板 translucent material 的测试位于 `test_partitioned_bridge_stage.py:802`，要求三块 bridge alpha 为 `0.80`。

## GLB 与浏览器产物

原仓库的 Pattern 2 Python 代码不包含 STEP-to-GLB 生产函数。`partitioned_bridge_stage.py:1392` 的 `sync_browser_bridge_translucency_artifacts(step_path)` 只在隐藏 GLB、motion JSON、sidecar 已经存在时读取 GLB 的 JSON chunk，识别透明叶节点，然后更新 motion / JS 的 bridge selectors；它不会创建 GLB。

CAD Explorer viewer 代码也将 `.<step-name>.glb` 视为既有 canonical STEP artifact：`skills/render/scripts/viewer/snapshot/index.mjs:581-583` 在缺少 GLB 时直接报错。故 GLB 的生产者不在本审计范围内可读到的 Pattern 2 生成代码，必须是仓库外/运行环境中的 STEP 转换工作流。已验收目录的写入时间顺序与此相符。

GLB 到位后，必须调用：

```python
sync_browser_bridge_translucency_artifacts(bridge_step_path)
```

随后才可用 CAD Explorer 的 snapshot workflow 生成 PNG。该 viewer snapshot workflow 消费既有 STEP + GLB + `.<step-name>.js`；它不替代 GLB 转换。

## 可一键编排的完整复现序列

以下是从原仓库可确定的 Python 编排核心。它将基础证据包、带桥板真实 STEP、独立 bridge checklist 写到同一输出目录；seed 取已验收的 `55330`，且启用实体镂空。

```python
from pathlib import Path

from models.watch_kinematic.watch_kinematic.power_chain_mvp import run_power_chain_mvp
from models.watch_kinematic.watch_kinematic.pattern_card_checklist import write_pattern2_checklist_artifacts
from models.watch_kinematic.watch_kinematic.partitioned_bridge_stage import (
    build_separate_display_partitioned_bridge_stage,
    sync_browser_bridge_translucency_artifacts,
)
from models.watch_kinematic.watch_kinematic.pattern_cards.separate_hour_minute_no_seconds import PATTERN_CARD_ID

output = Path("models/watch_kinematic/outputs/p2_seed_55330_complete_model")
seed = 55330

# 1. Pattern 2 solver / semantic / role / kinematic / validation / motion evidence.
base = run_power_chain_mvp(output, seed=seed, pattern_card_id=PATTERN_CARD_ID)

# 2. Full BREP assembly: three bridge plates, fasteners, and true lightening cuts.
stage = build_separate_display_partitioned_bridge_stage(
    output,
    seed=seed,
    include_lightening=True,
)

# 3. Independent recomputation of bridge gates and BREP-volume evidence.
checklist = write_pattern2_checklist_artifacts(output, seed=seed)

# 4. External CAD Explorer STEP->GLB conversion must run here.
#    It must create .watch_power_chain_separate_display_with_analytic_partitioned_bridges.step.glb.

# 5. After that GLB exists, rebind translucent bridge leaf selectors.
sync_browser_bridge_translucency_artifacts(stage["artifacts"]["step"])

# 6. CAD Explorer snapshot commands then create review PNGs from the STEP/GLB/JS trio.
```

步骤 4 不是可从本原仓库 Pattern 2 源码还原出的函数调用，因而严格说“所有真实工件”的单命令复现目前缺少外部 GLB converter 的明确入口。Python 侧完整链可一键；包含 GLB 和截图的端到端一键链需要把实际 CAD Explorer 转换服务/CLI 显式纳入一个外层脚本。

## 验证佐证

`models/watch_kinematic/tests/test_partitioned_bridge_stage.py:200` 直接调用 stage builder，并断言：STEP 存在、三块 bridge label 存在、seam gap 满足要求、CAD 不使用 grid contour。`test_partitioned_bridge_stage.py:488` 与 `:511` 分别检查镂空不侵入 upper-bearing keepout、且 fastener 周边保留最小制造 web。这证实 stage builder 覆盖了真实桥板与镂空实体，但没有改变上文关于 semantic / role / kinematic / validation 产物缺席及无 GLB producer 的结论。
