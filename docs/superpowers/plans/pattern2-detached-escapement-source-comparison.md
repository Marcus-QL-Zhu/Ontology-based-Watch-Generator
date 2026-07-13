# Pattern 2 外部擒纵机构悬空根因调查

## 结论

目标 STEP 中的悬空叶子实体**不是** Pattern 2 的已验收/完整 STEP 所具有的几何，也不是 GLB、CAD Explorer 或浏览器同步阶段造成的显示问题。根因在于**临时 `git archive` 捕获环境使用了未锁定的全局 Python / build123d 0.11.1，而原项目环境为 build123d 0.10.0**。这使源代码中对外部 STEP 的递归叶子提取路径在该环境下丢失了部分导入装配层级的 placement；随后代码又把这些局部叶子逐一 scale/rotate/translate 后扁平导出，故一批辅助实体保留了错误的局部坐标并在 Y/Z 方向散开。

分类：**主要责任是临时 archive 执行环境的未锁定 CAD 依赖；源 generator 含有被该依赖差异触发的兼容性脆弱点。**不是 capture 阶段的 STEP-to-GLB / browser-sync 后处理。capture 编排是把该环境差异带入结果的通道，但不直接改写 STEP 几何。

## 对照对象的确定

不能只按目录名认定“已验收”。本次采用下面这一份原项目 Pattern 2 完整 STEP 作为与目标同 seed 的直接对照：

```text
C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display/models/watch_kinematic/outputs/p2_seed_55330_complete_model/watch_power_chain_separate_display_with_analytic_partitioned_bridges.step
```

证据链：

1. 同目录 `separate_display_partitioned_bridge_stage_report.json:2-11` 标明 `pattern_card_id=separate_hour_minute_no_seconds_v1`、`status=pass`、`seed=55330`，并把该 STEP、motion、JS 和 report 作为同一完整桥板阶段工件列出；`:13-17` 又标明桥板阶段通过。
2. 原项目的已知验收记录 `knowledge_base/case_studies/cad_explorer_windows_snapshot_lessons.md:25-26` 明确记载：Pattern 2 seed `55330` 的模型已完成 iso/top/front CAD Explorer 快照自检。因此这是“用户验收/完整”输出的可追溯工件，而非仅凭 `p2_seed_...` 名称猜测。
3. 该工件 SHA-256 是 `559272488077a8526e48f45520f50ec1afbde701703752aca908d7df31dfeaab`。目标工件是 `ccda8363b99ad0163bc38bf767866e21a8e4fdc6e301c85322983256e2c87db2`，所以两者不是同一导出文件。

说明：迁移仓库后来的严格正式链记录把 `55330` 的基础工程阶段判为不合格，并以 `8459` 作为“所有正式阶段均 pass”的迁移基线（`docs/architecture/reference-baseline-contract.md:17-21`，以及 `docs/superpowers/plans/task-2-orchestration-baseline-report.md:9-27`）。这不推翻上面的可视验收/完整输出身份；它表示“视觉完整的 55330 工件”与“迁移用全部硬门禁通过 baseline”是两件不同的事。本调查针对目标同样报告为 seed `55330` 的 STEP，故同 seed 对照最有证明力。

## 几何与 occurrence 证据

使用只读 CAD inspect 对三个工件作了 STEP 级检查：目标、原项目同 seed 完整 STEP，以及原项目严格迁移 baseline 的 `p2_fix8459` STEP。

| STEP | occurrence / leaf | 全局包围盒 mm | 结论 |
| --- | ---: | --- | --- |
| 目标临时 STEP | 127 / 126 | min `[-26.544151,-21.9988,-23.867804]`, max `[22.0,90.315333,13.663199]` | Y 112.314、Z 37.531，明显超出机芯包络 |
| 原项目 seed 55330 完整 STEP | 327 / 126 | min `[-22.0,-21.9988,-0.675]`, max `[22.0,21.9995,5.16]` | 44 mm 表壳/主夹板包络内 |
| 原项目 seed 8459 完整 STEP | 254 / 128 | min `[-22.0,-21.9985,-0.675]`, max `[22.0,21.9978,5.16]` | 同样在正确包络内 |

叶子数基本相同而 occurrence 层次从 `327` 降为 `127`，说明目标并非少了外部擒纵机构，而是导出时装配层级/placement 表达发生变化。目标 STEP 的 `PRODUCT` 标签仍包含完整的外部叶子集合，例如 `external_escape_wheel`、`external_pallet_fork`、`external_balance_wheel`、`external_hairspring`、`external_escapement_reference_plate`、`external_escape_staff` 和 `external_escapement_auxiliary_solid_06...34`；参见目标 STEP 的 ISO-10303-21 `PRODUCT` 记录约第 `390253`、`396009`、`398896`、`407517`、`412032`、`418468` 行及其后续 auxiliary records。

目标 sidecar 也把这些标签映射为 `#o1.78` 至 `#o1.110`（`.watch_power_chain_separate_display_with_analytic_partitioned_bridges.step.js:1069-1645`）。这恰好证明语义/动画映射仍认为外部擒纵机构在位，却没有验证其实际包围盒。

核心叶子中，外部 escape wheel、pallet fork、balance wheel、hairspring 与 reference plate 的 `#o1.78...82` 仍在正确区域；出错的是同一外部导入 STEP 中的一批 staff、cap、hardware 和 auxiliary leaves。典型目标中心点与已验收 seed 55330 的同 occurrence 对比如下（mm）：

| occurrence / label | 目标中心 | 已验收中心 |
| --- | --- | --- |
| `o1.83 external_escape_staff` | `[5.213,2.170,-22.671]` | `[5.213,2.170,0.728]` |
| `o1.84 external_escapement_auxiliary_solid_06` | `[-10.247,89.877,-16.315]` | `[4.310,7.291,-0.072]` |
| `o1.88 external_escape_upper_cap` | `[5.213,2.170,7.029]` | `[5.213,2.170,1.379]` |
| `o1.91 external_escape_upper_fixed_hardware` | `[5.213,2.170,13.430]` | `[5.213,2.170,1.659]` |
| `o1.100 external_escapement_auxiliary_solid_25` | `[-6.775,70.181,-16.291]` | `[4.513,6.141,-0.048]` |
| `o1.104 external_escapement_auxiliary_solid_29` | `[-6.775,70.181,-19.224]` | `[4.513,6.141,-0.203]` |
| `o1.109 external_escapement_auxiliary_solid_34` | `[-0.800,36.284,-6.062]` | `[4.862,4.161,0.576]` |

按已验收表壳包络 `x=[-22,22]`、`y=[-21.9988,21.9995]`、`z=[-0.675,5.16]` 筛查，目标的 126 个叶子中有 **26 个**越界，均为上表所示 family 的外部 escapement leaves。故“沿 Z 排开”的观察来自真实 STEP B-Rep placement，非 viewer camera、透明度或 GLB 分组。

## 源代码与执行边界逆向追踪

### 原 generator 的正常意图

`models/watch_kinematic/watch_kinematic/external_escapement_replacement.py:169-212`：

- `build_external_escapement_parts()` 读取外部 `Escapement Model.STEP`；
- 对每个 `source_solid` 依次 `scale`、`rotate(Z)`、`translate(fit["translation_mm"])`（`:174-185`）；
- 生成带 `external_swiss_lever_escapement_replacement` 标签的 compound（`:194-212`）。

`power_chain_mvp.py:1193-1252` 把这个 compound 作为 Pattern 2 装配 child 加入。`partitioned_bridge_stage.py:340-415` 则调用该装配、以 `_flatten_for_step_color_sync()` 得到语义叶子并 `bd.export_step()`；关键路径是 `:377-384`。递归 flatten 本身不重建 parent placement，只取 `node.children` 的末端 leaf（`:1354-1362`）。因此它要求 `bd.import_step()` 返回的每个 leaf 已经携带从外部装配祖先继承的全局 location。

这正解释了故障形态：主 wheel/plate leaves 的位置恰好正确，但外部源 STEP 中带额外装配层级的 auxiliary/staff/cap leaves 失去祖先 placement 后，仍以局部坐标参与最终 `scale/rotate/translate`，形成 `y=36/70/90` 与大幅正负 Z 的分散阵列。

### capture 的实际运行环境

迁移 capture 明确冻结的是相同 source commit `5f0e9b91786a834c1119037b66d404027a227d8a`：

- `scripts/capture_reference_baseline.py:28` 固定 commit；`:148-163` 用 `git archive` 解到临时 snapshot；`:517-520` 在该 snapshot 上运行正式链。
- `scripts/reference_orchestration.py:262-280` 把 snapshot 放入 `PYTHONPATH`，但在 `:271-274` 用宿主 `sys.executable` 执行 driver；没有指定原项目 `.venv`。
- 新仓库 `pyproject.toml:10-14` 只声明未定版的 `build123d`。实际检查到原项目 `.venv` 的 build123d 是 **0.10.0**，而执行 `python`（宿主 `C:/Users/wande/AppData/Local/Programs/Python/Python311/python.exe`）载入的是 **0.11.1**。

源代码相同而 B-Rep 结果不同，且目标就是该 archive capture 输出目录；这排除了“源 generator 最近改坏”的解释。更准确地说，generator 的递归 leaf-flatten 实现对 build123d 的 imported-assembly location 语义有隐含依赖，未锁定依赖的 archive 环境把该潜在兼容性问题变成了实际损坏工件。

外部 reference STEP 是 Git LFS 对象：`git ls-tree` 对该 commit 显示 132-byte pointer，而已 materialize 的源文件 SHA-256 为 `313e49a2c323b84d68c2aa47df92ef0c1368338601df83cc9e320cde751c4eae`、大小 `1,190,969` bytes。capture 没有把 LFS materialization/hash 写入 baseline；这也是 archive 环境不可复现实体验证的一部分。不过，目标具有全部 41 个外部 leaf 的同一标签族，且主五个叶子位置正确，现有证据不支持“缺 LFS asset”是本次大批错位的直接原因。

## 非根因排除

1. **不是 GLB/Viewer 后处理。** 目标 STEP 在 `.glb`（09:38）和 browser-sync JS/motion（09:38）之前已于 09:37 写出；错位直接由 STEP inspect 检出。`reference_orchestration.py:493-500` 的 GLB 转换发生在 final STEP 后，`:531-542` 的 sync 只在该 STEP 的 motion/JS sidecars 上工作。
2. **不是仅 viewer 的 occurrence 名称显示问题。** ISO-10303-21 B-Rep 的整体 bbox 和按 occurrence 的 bbox 已经越界；GLB 只是继承这一几何。
3. **不是 Pattern 2 完整链缺少 external escapement。** 目标 report `separate_display_partitioned_bridge_stage_report.json:4-6` 为 `pass`/seed `55330`，STEP 也含完整 external label family；错误是叶子 placement，不是 omission。
4. **不是 source commit 漂移。** capture 固定 `5f0e9b...`，而只读 source worktree 的 `HEAD` 也是该 commit；差异发生在解释器/CAD dependency 与导出结果。

## 可复现性缺口（本次不修改）

当前 capture 的通过条件只检查阶段 status、sidecar 存在、hash 和 PRODUCT label 集合（`capture_reference_baseline.py:195-202, 426-507`）。它没有记录 Python/build123d/OCCT 版本、LFS materialization hash，也没有对最终 STEP 的全局 envelope、外部 leaf placement 或目标轴距离做门禁。因此一个 `status=pass` 的 capture 可以产出本案这种错误 STEP，而 GLB 和浏览器同步会继续成功。

本报告仅记录只读调查结论，未修改 source、capture、工件或依赖环境。
