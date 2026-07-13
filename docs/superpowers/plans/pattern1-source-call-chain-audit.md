# Pattern 1 Source Call-Chain Audit

Date: 2026-07-12

## Scope And Evidence

This is a read-only audit of the source worktree:

```text
C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display
```

No source or generated file in that worktree was modified. The strongest available acceptance evidence is the Pattern 1 entry map, which calls Pattern 1 the accepted base watch scheme, plus the shared-worktree migration report. The report identifies this regenerated, latest-capability artifact as its validation model, with `seed=731`, `include_lightening=True`, generator status `pass`, three bridges, and a successful CAD inspection:

```text
models/watch_kinematic/outputs/shared_pattern1_latest_seed_731_full_model/
  watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step
  analytic_partitioned_bridge_stage_report.json
  watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.motion.json
  .watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step.js
  .watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step.glb
```

The report's generated-model statement is in:

```text
docs/design_patterns/sprints/watch_kinematic_demo/pattern_cards/watch_generator_shared_worktree_migration_report.md
```

There is no machine-readable record that literally says `user_accepted`. Therefore this directory is an evidence-based choice, not proof of an individual approval event. `p1_seed_5908_complete_model/` is a later full-model output (2026-07-07) with a passing bridge-stage report, but no stronger acceptance marker was found.

## Conclusion

`run_power_chain_mvp` is **not** the complete Pattern 1 deliverable entry. It is the Phase 1, no-bridge compatibility/MVP entry, despite accepting `include_bridges=True`. It produces the base assembly and the only standard Pattern 1 emission point for the base solver, semantic, role-contract, kinematic, and validation JSON files. The accepted full STEP instead comes from `build_partitioned_bridge_stage`, which bypasses `run_power_chain_mvp` and directly calls the private `_build_design` function.

The full deliverable chain therefore has two layers:

1. The Phase 1 evidence path (`run_power_chain_mvp`) writes the complete base-model engineering reports.
2. The final CAD path (`build_partitioned_bridge_stage`) independently rebuilds the same seeded design, adds analytic bridges, imports the external Swiss-lever solids, emits the final STEP and final STEP motion sidecars, and then requires a separate CAD STEP-tool invocation to create the hidden GLB topology artifact.

## Reverse Trace From The Accepted Full STEP

```text
shared_pattern1_latest_seed_731_full_model/
  final STEP + alias STEP
  <- partitioned_bridge_stage.build_partitioned_bridge_stage(
       output_dir, seed=731,
       layout_id="shared_pattern1_latest_seed_731_full_model",
       include_lightening=True)
       |
       +-- power_chain_mvp._build_design(seed, include_bridges=False)
       |     +-- current_pattern_solver.solve_current_pattern(
       |           seed, case_inner_radius_mm=CASE_RADIUS_MM,
       |           bridge_perimeter_reserved_band_mm=...)
       |           -> selected Pattern 1 axes/gears/proofs
       |
       +-- build_analytic_bridge_stage_plan(design, layout_id)
       |     +-- bridge_xy_partition.solve_bridge_xy_partition(..., grid_resolution=121)
       |     +-- analytic local-lobe bridge plan: barrel/train/escapement bridges
       |
       +-- bridge_lightening.solve_bridge_lightening_plan(...) [only when True]
       +-- external_escapement_replacement.build_external_escapement_parts(design)
       |     -> selected external Swiss-lever STEP solids and generated balance-axis replacement
       +-- _build_base_without_old_bridges + _make_analytic_bridge_stage
       +-- build123d.export_step(final STEP and alias STEP)
       +-- power_chain_mvp.write_power_chain_motion_artifacts(..., external_escapement=True)
       |     -> final .motion.json and hidden .step.js
       +-- external_escapement_replacement._build_validation_report(...)
       |     -> embedded in analytic_partitioned_bridge_stage_report.json
       +-- report JSON
       |
       +-- later, outside this Python builder:
             python -m skills.cad.scripts.step <final STEP> --kind assembly
             -> hidden .step.glb
             -> sync_browser_bridge_translucency_artifacts(<final STEP>)
             -> rewrites final motion JSON and .step.js to the GLB leaf IDs
```

The Pattern 1 package facade is the public solving/card-facing entry, but is not yet the full CAD builder:

```text
pattern_cards/central_hour_minute_offcenter_seconds/solver.py
  solve_current_pattern_layout(...)
  -> current_pattern_solver.solve_current_pattern(...)

pattern_cards/central_hour_minute_offcenter_seconds/card.py
  build_current_pattern_card(), write_current_pattern_card(...)

pattern_cards/central_hour_minute_offcenter_seconds/review.py
  write_current_pattern_review(...)
  -> solve_current_pattern_layout(...)
```

`current_pattern.py` only re-exports that package for compatibility. Neither the package nor `current_pattern.py` calls the full STEP builder.

## Calls By Responsibility

| Responsibility | Primary function and source | Inputs | Writes |
| --- | --- | --- | --- |
| Pattern card | `build_current_pattern_card`, `write_current_pattern_card` in `pattern_cards/central_hour_minute_offcenter_seconds/card.py` | `output_dir` | `<pattern-id>.json`, `<pattern-id>.md` |
| Public Pattern 1 solve | `solve_current_pattern_layout` in `pattern_cards/.../solver.py` | `seed`, optional solver overrides | Returns solver report only |
| Actual solver | `solve_current_pattern` in `current_pattern_solver.py` | `seed=123`, `case_inner_radius_mm=22.0`, `bridge_perimeter_reserved_band_mm=2.0`, optional `candidate_limit` | Returns candidate/proof report only |
| Phase 1 CAD and base evidence | `run_power_chain_mvp` in `power_chain_mvp.py` | `output_dir`, `seed`, `include_bridges=False`, `pattern_card_id=None` | base STEP, solver, semantic, role-contract, kinematic, validation JSON, dashboard |
| External reference semantics | `run_escapement_reference_semantics` in `escapement_reference.py` | `output_dir`, `seed` | external-reference semantic, role, axes, envelope, motion-constraint, validation JSON |
| External escapement replacement | `build_external_escapement_replacement` in `external_escapement_replacement.py` | `output_dir`, `seed`, `include_bridges=False` | selected external-parts STEP, replacement STEP and alias, fit report, role map, validation, motion JSON, hidden STEP JS |
| External replacement with legacy bridges | `build_external_escapement_bridge_stage` in `external_escapement_replacement.py` | `output_dir`, `seed` | calls preceding function with `include_bridges=True`; not the accepted analytic bridge path |
| Accepted full Pattern 1 CAD | `build_partitioned_bridge_stage` in `partitioned_bridge_stage.py` | `output_dir`, `seed=42`, `layout_id="seed_42_layout_01"`, `include_lightening=False` | final analytic-bridge STEP + alias, final motion JSON, hidden STEP JS, bridge-stage report |
| STEP motion / `step.js` | `write_power_chain_motion_artifacts` in `power_chain_mvp.py` | STEP path, in-memory design, `external_escapement`, optional feature refs | `<step-stem>.motion.json`, `.<step-name>.js` |
| GLB | `python -m skills.cad.scripts.step <STEP> --kind assembly` | final STEP, direct-import kind required | `.<step-name>.glb` (CAD Explorer topology sidecar) |
| GLB-to-browser bridge binding | `sync_browser_bridge_translucency_artifacts` in `partitioned_bridge_stage.py` | final STEP after GLB exists | rewrites final motion JSON and hidden STEP JS; returns `False` if prerequisites/change are absent |

## What `run_power_chain_mvp` Does And Does Not Do

For Pattern 1 (`pattern_card_id is None` or `central_hour_minute_with_off_center_seconds_v1`), `run_power_chain_mvp` calls, in order:

```text
_build_design
_build_independent_geometry_report
_build_assembly
_build_semantic_report
_build_kinematic_report
_build_role_contract_report
_build_validation_report
export_step
```

It writes `watch_power_chain_mvp.step` when `include_bridges=False`, or `watch_power_chain_with_bridges.step` when `True`, alongside its base reports. `PHASE` remains `power_chain_mvp_no_bridges`, and its own validation report explicitly treats generated bridges as excluded by design. It does not:

- create the analytic-partitioned bridge geometry used by the accepted full STEP;
- invoke `build_analytic_bridge_stage_plan` or bridge lightening;
- replace its placeholder escapement with the selected external Swiss-lever solids;
- write the accepted final STEP basename;
- create a GLB;
- run the post-GLB translucency synchronization.

It is consequently an important intermediate evidence entry, not an end-to-end Pattern 1 delivery command.

## Reproducible One-Key Sequence

Run the following PowerShell block from the original worktree root. It intentionally writes to a new output directory, never to the accepted evidence directory. It emits the base reports, explicit external-escapement reports, the full accepted-style STEP, STEP JS/motion, the GLB, and final GLB leaf-ID synchronization.

```powershell
$py = '.\.venv\Scripts\python.exe'
$out = 'models/watch_kinematic/outputs/pattern1_seed_731_full_audit_repro'

& $py -c @"
from pathlib import Path

from models.watch_kinematic.watch_kinematic.pattern_cards.central_hour_minute_offcenter_seconds import solve_current_pattern_layout
from models.watch_kinematic.watch_kinematic.power_chain_mvp import run_power_chain_mvp
from models.watch_kinematic.watch_kinematic.escapement_reference import run_escapement_reference_semantics
from models.watch_kinematic.watch_kinematic.external_escapement_replacement import build_external_escapement_replacement
from models.watch_kinematic.watch_kinematic.partitioned_bridge_stage import build_partitioned_bridge_stage

out = Path(r'$out')
seed = 731
layout_id = 'pattern1_seed_731_full_audit_repro'

solver = solve_current_pattern_layout(seed=seed)
assert solver['status'] == 'pass' and solver['selected_candidate'] is not None, solver

phase1 = run_power_chain_mvp(out, seed=seed)
assert phase1['status'] == 'pass', phase1

escapement_semantics = run_escapement_reference_semantics(out, seed=seed)
assert escapement_semantics['status'] == 'pass', escapement_semantics

replacement = build_external_escapement_replacement(out, seed=seed, include_bridges=False)
assert replacement['status'] == 'pass', replacement

full = build_partitioned_bridge_stage(
    out,
    seed=seed,
    layout_id=layout_id,
    include_lightening=True,
)
assert full['status'] == 'pass', full
print(full['artifacts']['step'])
"@

$final = Join-Path $out 'watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step'
& $py -m skills.cad.scripts.step $final --kind assembly

& $py -c @"
from pathlib import Path
from models.watch_kinematic.watch_kinematic.partitioned_bridge_stage import sync_browser_bridge_translucency_artifacts

step = Path(r'$final')
assert step.with_name('.' + step.name + '.glb').exists()
assert sync_browser_bridge_translucency_artifacts(step)
"@
```

Expected final output inventory under `$out`:

```text
watch_power_chain_mvp.step
watch_power_chain_mvp.solver.json
watch_power_chain_mvp.semantic.json
watch_power_chain_mvp.role_contracts.json
watch_power_chain_mvp.kinematic.json
watch_power_chain_mvp.validation.json
watch_escapement_reference.semantic.json
watch_escapement_reference.role_contracts.json
watch_escapement_reference.axes.json
watch_escapement_reference.envelopes.json
watch_escapement_reference.motion_constraints.json
watch_escapement_reference.validation.json
watch_power_chain_with_scaled_swiss_lever_reference.step
swiss_lever_escapement_selected_external_parts.step
swiss_lever_escapement_fit_report.json
watch_external_escapement_replacement.role_map.json
watch_external_escapement_replacement.validation.json
watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step
watch_power_chain_layout01_analytic_partitioned_bridges.step
watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.motion.json
.watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step.js
.watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step.glb
analytic_partitioned_bridge_stage_report.json
```

## Important Current-Source Caveats

- `build_partitioned_bridge_stage` has no hard stop for `bridge_stage.seam_policy.minimum_plate_gap_status`. The accepted-style report can have top-level `status: pass` while its embedded seam-gap subcheck is `fail`. This is observable in `shared_pattern1_latest_seed_731_full_model/analytic_partitioned_bridge_stage_report.json` (`0.9902 mm` observed versus `1.4 mm` required for the barrel/train pair). The top-level status is driven by external-escapement validation only.
- The final builder does not write Pattern 1 semantic/role/kinematic JSON itself. The one-key sequence explicitly preserves those from the Phase 1 branch in the same directory.
- `sync_browser_bridge_translucency_artifacts` has no call site in the source worktree. It must be invoked after, not before, the STEP CLI creates the hidden GLB; otherwise bridge `partIds` in the final motion/browser sidecars are not re-bound to the actual GLB leaf occurrences.
- The external reference semantic writer and the external replacement builder are separate. The former provides reference-level semantic/role/motion evidence; the latter supplies imported solids, fit/role-map evidence, replacement validation, and a replacement STEP. The final analytic bridge builder uses `build_external_escapement_parts` directly, rather than calling either public wrapper.
