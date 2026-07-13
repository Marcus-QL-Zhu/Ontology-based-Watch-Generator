# Pattern 3 Source Call-Chain Audit

## Scope and conclusion

This is a read-only trace of the original worktree:

`C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display`

The original entry map calls `independent_hour_minute_no_seconds` **Pattern 3** and reserves `pattern4_independent_hour_minute_no_seconds` for the later hard-gated one-key delivery wrapper. The current Pattern 3 source package is therefore:

`models/watch_kinematic/watch_kinematic/pattern_cards/independent_hour_minute_no_seconds/`

The accepted Pattern 3 complete-model outputs are represented by:

`models/watch_kinematic/outputs/independent_display_seed_731_full_model/`

and, after the service-span correction:

`models/watch_kinematic/outputs/independent_display_seed_731_service_spans_fix/`

Both contain the full STEP, motion JSON, STEP-module JS, hidden Explorer GLB/topology sidecar, and bridge-stage report. The report status is `pass`; the latter output has lightening enabled.

## Direct Pattern 3 complete-model chain

```text
build_independent_display_partitioned_bridge_stage(output_dir, seed, include_lightening)
  -> Pattern 3 solve_independent_display_layout(seed)
  -> power_chain_mvp._build_independent_display_design(seed, solver_report)
  -> build_independent_display_bridge_stage_plan(design, layout_id)
     -> bridge_xy_partition.solve_bridge_xy_partition(...)
     -> separate_display_axis_voronoi_probe._axis_voronoi(...)
     -> separate_display_axis_voronoi_probe._axis_voronoi_seam_plan(...)
     -> _separate_display_continuous_region_footprints(...)
     -> _bridge_record(...): bridges, support pads, screws, bearings
  -> [when requested] bridge_lightening.solve_bridge_lightening_plan(...)
  -> power_chain_mvp._build_separate_display_assembly(design)
     -> _make_mainplate / _make_arbors_and_lower_seats / _make_barrel /
        _make_gear / _make_display_works / _make_analytic_bridge_stage /
        external escapement geometry
  -> build123d.export_step(assembly, STEP)
  -> power_chain_mvp._build_independent_display_motion_report(...)
  -> power_chain_mvp._build_independent_display_semantic_report(design)
  -> power_chain_mvp._build_independent_display_validation_report(design, semantic, motion)
  -> power_chain_mvp._render_step_module_js(motion)
  -> write motion JSON, hidden `.step.js`, aggregate bridge-stage report
```

The top-level implementation is `partitioned_bridge_stage.py:513-591`. It explicitly documents itself as “Generate Pattern 3 with external escapement and analytic bridge plates.”

### Solver and design facts

1. `pattern_cards/independent_hour_minute_no_seconds/solver.py:47` defines `solve_independent_display_layout`. It enumerates deterministic seed-ordered candidate placements, calls `_build_independent_display_candidate` (`:118`), and returns the first `status == "pass"` candidate.
2. Candidate construction uses `_solve_base_train_axes`, `_display_gears`, `_display_meshes`, `_power_branches`, `_display_ratio_proof`, and geometry proofs including case clearance, display-axis separation, same-layer non-mesh clearance, and foreign-axis gear keepout (`:253-650`).
3. `power_chain_mvp._build_independent_display_design` (`power_chain_mvp.py:675`) promotes the selected solver candidate into the 3D design dictionary: axes, train/display gears, mesh phases, z stack, mount stacks, external escapement references, and independent display motion works.

### Full bridge and opening geometry

1. `build_independent_display_bridge_stage_plan` (`partitioned_bridge_stage.py:418-510`) sets the independent bridge groups: `barrel_bridge`, `train_bridge`, and `escapement_bridge`. The train bridge owns the complete independent minute and hour branch arbor set.
2. It calls `solve_bridge_xy_partition` (`bridge_xy_partition.py`) only as a search/feasibility source; the returned plan explicitly says `grid_contour_used_for_cad: false`.
3. It combines the grid facts with `_axis_voronoi` and `_axis_voronoi_seam_plan`, then builds final native-smooth bridge footprints with `_separate_display_continuous_region_footprints` and `_bridge_record`.
4. `bridge_lightening.solve_bridge_lightening_plan` is conditional in the Pattern 3 stage (`:534-547`). It writes `manufacturing_windows` and fastener-web-clearance facts into each bridge record. `include_lightening=False` is the Pattern 3 function default, so it is not a delivery-safe default by itself.
5. CAD solids are made by `power_chain_mvp._build_separate_display_assembly` (`:1193`), which calls the generic geometry builders and, because `design["bridges_generated"]` is true, includes `_make_analytic_bridge_stage`. The smooth bridge boundaries and smooth lightening-window extrusions are implemented in `partitioned_bridge_stage._make_analytic_bridge_stage` (`:1873`), `_extrude_smooth_bridge_boundary` (`:1949`), and `_extrude_smooth_lightening_window_boundary` (`:1966`).

The function name `_build_separate_display_assembly` is historical/shared; with an independent design dictionary it is the actual complete Pattern 3 assembly builder, not a Pattern 2-only geometry path.

## Artifact ownership

| Artifact | Producing function/script | Written by the complete Pattern 3 stage? |
| --- | --- | --- |
| Solver report | `solve_independent_display_layout`; standalone writer only in `power_chain_mvp._run_independent_display_power_chain_mvp` (`:476-526`) | No standalone file; selected solver facts are embedded in design/report validation |
| Semantic report | `_build_independent_display_semantic_report` (`:1353`) | Computed, then embedded only through validation; no `.semantic.json` |
| Kinematic report | `_build_independent_display_kinematic_report` (`:1732`) | Not called by the complete bridge-stage path; no `.kinematic.json` |
| Role contracts | `_build_independent_display_role_contract_report` (`:1594`) | Not called by the complete bridge-stage path; no `.role_contracts.json` |
| Validation report | `_build_independent_display_validation_report` (`:1452`) | Yes, embedded as `validation` in `independent_display_partitioned_bridge_stage_report.json` |
| Motion JSON | `_build_independent_display_motion_report` (`:1904`) | Yes, `<step-stem>.motion.json` |
| STEP-module JS | `_render_step_module_js` (`:6684`) and `_step_module_sidecar_path` (`:6220`) | Yes, hidden `.<step-name>.js` |
| STEP | `build123d.export_step` at `partitioned_bridge_stage.py:557` | Yes |
| Explorer GLB/topology | `skills/cad/scripts/step` -> `common.generation._generate_part_outputs` -> `export_assembly_glb_from_scene` | No; this is a required post-STEP CAD-skill operation |
| Browser translucency rebinding | `sync_browser_bridge_translucency_artifacts` (`partitioned_bridge_stage.py:1392-1406`) | No; required after GLB generation when it changes bridge leaf bindings |

The independent MVP runner is the only existing original function that writes all standalone evidence files, but it is not a complete bridge model:

`run_power_chain_mvp(..., pattern_card_id="independent_hour_minute_no_seconds_v1")`

Its `_run_independent_display_power_chain_mvp` branch writes STEP, solver, semantic, kinematic, motion, validation, role-contract, dashboard, and JS artifacts (`power_chain_mvp.py:476-526`), but calls `_build_separate_display_assembly` before any bridge-stage plan and therefore does not produce the analytic bridge plates or lightening openings. It must not be presented as the full Pattern 3 delivery path.

## GLB sidecar chain

The accepted `independent_display_seed_731_full_model` directory contains:

```text
watch_power_chain_independent_display_with_analytic_partitioned_bridges.step
watch_power_chain_independent_display_with_analytic_partitioned_bridges.motion.json
.watch_power_chain_independent_display_with_analytic_partitioned_bridges.step.js
.watch_power_chain_independent_display_with_analytic_partitioned_bridges.step.glb
independent_display_partitioned_bridge_stage_report.json
```

The hidden `.step.glb` is not emitted by the Pattern 3 Python generator. It is the CAD Explorer topology artifact produced by the repository CAD launcher. The relevant chain is:

```text
skills/cad/scripts/step/cli.py:107 main
  -> common.generation.generate_step_targets
  -> common.generation._generate_part_outputs
  -> load_step_scene + mesh_step_scene + extract_selectors_from_scene
  -> export_assembly_glb_from_scene
  -> .<step-name>.glb
```

`skills/cad/references/step-generation.md` confirms that the launcher creates the adjacent hidden Explorer GLB/topology artifact by default. The `--kind assembly` argument is required for a direct `.step` target. `--skip-explorer` must not be used.

After that launcher finishes, `sync_browser_bridge_translucency_artifacts(step_path)` reads the GLB JSON material/node mapping, updates the motion feature references for translucent bridge leaves, and rewrites both the motion JSON and `.step.js`. It does not create a GLB; it is a post-GLB synchronization pass.

## `build_pattern4_independent_display_complete_model` classification

`build_pattern4_independent_display_complete_model` (`partitioned_bridge_stage.py:594-707`) is **not a lower-level bridge stage function**. It is the original repository’s Pattern 4 top-level, hard-gated completion wrapper.

Evidence:

1. It imports the distinct `pattern4_independent_hour_minute_no_seconds` solver/card rather than the Pattern 3 card (`:603-607`).
2. It runs the Pattern 4 solver before all geometry and writes a failure report immediately when no candidate passes (`:616-631`).
3. It reuses the Pattern 3 bridge-plan implementation (`build_independent_display_bridge_stage_plan`) rather than defining a separate bridge-plan implementation (`:633-635`). This reuse does not make it a stage function.
4. It computes motion, semantic, and validation before export; `_pattern4_hard_gate_report` must have `status == "pass"` before STEP/motion/JS are written (`:669-706`).
5. Its report policy is `export_step_only_after_all_hard_validation_checks_pass`; a test proves that a forced validation failure leaves no STEP (`tests/test_partitioned_bridge_stage.py:171-198`).
6. Its current default is `include_lightening=True` (`:594-600`), changed by commit `6f813cda` and then refined in `ba4799e5`.

Therefore, in any migration where “new Pattern 3” is renamed from the original independent/P4 delivery concept, this function is the correct top-level one-key generator to preserve the original hard gate and default lightened-bridge delivery behavior. The shared bridge-plan function beneath it remains the stage-level primitive.

## Reproducible complete-delivery sequence

For the original accepted hard-gated product, use the Pattern 4 wrapper followed by the CAD Explorer GLB launcher and the bridge translucency synchronization. This is the shortest existing sequence that reproduces the real complete delivery artifact family (STEP + lightened complete bridge model + motion + JS + report + Explorer GLB):

```powershell
$root = 'C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display'
$out = "$root/models/watch_kinematic/outputs/repro_pattern4_seed_731"

& "$root/.venv/Scripts/python.exe" -c "from pathlib import Path; from models.watch_kinematic.watch_kinematic.partitioned_bridge_stage import build_pattern4_independent_display_complete_model; r=build_pattern4_independent_display_complete_model(Path(r'$out'), seed=731); assert r['status']=='pass', r"

& "$root/.venv/Scripts/python.exe" "$root/skills/cad/scripts/step" --kind assembly "$out/watch_power_chain_pattern4_independent_display_with_analytic_partitioned_bridges.step"

& "$root/.venv/Scripts/python.exe" -c "from models.watch_kinematic.watch_kinematic.partitioned_bridge_stage import sync_browser_bridge_translucency_artifacts as sync; assert sync(r'$out/watch_power_chain_pattern4_independent_display_with_analytic_partitioned_bridges.step')"
```

For strictly original Pattern 3 naming, replace the first command with:

```powershell
& "$root/.venv/Scripts/python.exe" -c "from pathlib import Path; from models.watch_kinematic.watch_kinematic.partitioned_bridge_stage import build_independent_display_partitioned_bridge_stage; r=build_independent_display_partitioned_bridge_stage(Path(r'$out'), seed=731, include_lightening=True); assert r['status']=='pass', r"
```

and change the STEP filename in the next two commands to:

`watch_power_chain_independent_display_with_analytic_partitioned_bridges.step`

Important limitation: the existing complete-model call chains deliberately do not produce standalone semantic, kinematic, role-contract, or solver JSON files. Their semantic and validation facts are embedded in the aggregate report/motion artifacts. There is no original one-key function that simultaneously creates (a) the full lightened bridge STEP/GLB delivery and (b) the complete standalone MVP evidence set. Producing both as a single coherent delivery would require a new wrapper or extending the top-level completion wrapper; that is outside this read-only audit.

## Source and output evidence inspected

- Original entry map: `docs/design_patterns/sprints/watch_kinematic_demo/pattern_cards/watch_pattern_1_to_4_entry_map.md`.
- Pattern 3 source: `models/watch_kinematic/watch_kinematic/pattern_cards/independent_hour_minute_no_seconds/{solver,card,review}.py`.
- Pattern 3/4 assembly, bridge, and export orchestration: `models/watch_kinematic/watch_kinematic/partitioned_bridge_stage.py`.
- Shared design, assembly, evidence, motion, and JS generators: `models/watch_kinematic/watch_kinematic/power_chain_mvp.py`.
- CAD Explorer GLB pipeline: `skills/cad/scripts/step/cli.py`, `skills/cad/scripts/common/generation.py`, and `skills/cad/scripts/common/glb.py`.
- Passing output reports/artifact sets: `models/watch_kinematic/outputs/independent_display_seed_731_full_model/`, `models/watch_kinematic/outputs/independent_display_seed_731_service_spans_fix/`, `models/watch_kinematic/outputs/p4_seed_85363_complete_model/`, and `models/watch_kinematic/outputs/pattern4_seed_731_gate_full/`.
