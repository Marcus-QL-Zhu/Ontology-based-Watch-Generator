# Pattern 2 External Swiss-Lever Escapement: Read-Only Root-Cause Investigation

Date: 2026-07-12

## Scope And Evidence

This is a read-only investigation of the failed Pattern 2 artifact:

```text
C:/Users/wande/AppData/Local/Temp/ontology-watch-pattern-02-2c6dda647efb4d53a2b16ae19c80f5b4/watch_power_chain_separate_display_with_analytic_partitioned_bridges.step
```

Source worktree:

```text
C:/Users/wande/.config/superpowers/worktrees/text-to-cad/codex-watch-separate-display
```

No generator, source asset, test, or existing artifact was changed. The only file written for this task is this report.

Evidence collected:

1. Imported the failed STEP and enumerated all 126 leaf occurrences and their bounding boxes.
2. Rebuilt only the in-memory Pattern 2 external-subassembly transform for seed `55330`; no STEP was exported.
3. Compared the external compound before flattening, after `_flatten_for_step_color_sync`, and after importing the failed STEP. Their external bounding boxes agree.
4. Inspected the source asset's imported solids and `Location` objects.
5. Compared checked-in Pattern 1 and Pattern 4 complete STEP artifacts that contain the same 34 external occurrence labels.
6. Visually self-checked the supplied Pattern 2 isometric PNG. It shows the remote vertical hardware stack above and below the watch, consistent with the measured locations.

## Data Flow

```text
Escapement Model.STEP
  -> bd.import_step(SOURCE_STEP)
  -> _leaf_shapes(imported): 35 source solids, each with local geometry plus Location
  -> build_external_escapement_parts()
       excludes source indices 11, 14, 18
       applies Shape.scale(s), Z rotation, and translation to each remaining leaf
       produces 32 imported leaves + 2 generated balance replacements
  -> p._build_separate_display_assembly()
       appends the external Compound as one assembly child
  -> _flatten_for_step_color_sync()
       returns semantic leaf parts for STEP colour binding
  -> bd.Compound(children=assembly_children)
  -> bd.export_step(...Pattern 2 STEP)
```

Relevant implementation points:

- Source asset and source-index mapping: `external_escapement_replacement.py:16-82`.
- Import and recursive leaf extraction: `external_escapement_replacement.py:276-291`.
- Per-leaf transform: `external_escapement_replacement.py:169-197`.
- Pattern 2 insertion into the assembly: `power_chain_mvp.py:1193-1251`.
- Pattern 2 flatten/compound/export boundary: `partitioned_bridge_stage.py:377-384`.
- Flattening implementation: `partitioned_bridge_stage.py:1354-1371`.

## Fit Contract

For the failed seed, the code computes this intended global similarity placement:

```text
scale s                         = 0.058388178774657525
rotation about Z                = 9.996873840762763 deg
translation                     = (5.213, 2.1696, 0.9821960838628423) mm
reference-plate lower face      = -0.025000 mm
mainplate top                   = -0.025000 mm
recorded plate mate gap         = 0.000000 mm
```

The intended operation is a full similarity transform, including every imported occurrence's placement. The implementation instead calls `source_solid.scale(s)` and then rotates/translates that `Shape`.

## Observed Failure

`bd.import_step()` returns the source hardware leaves as individually located solids. For example, source leaf `6` is a washer with:

```text
raw Location              = (0.000000, 89.060000, -17.250000) mm
after Shape.scale(s)      = (0.000000, 89.060000, -17.250000) mm
after Z rotate/translate  = (-10.247321, 89.877422, -16.267804) mm
```

The geometry dimensions scale, but `Shape.scale(s)` does **not** scale the `Location` translation. The following Z rotation and translation therefore operate on the unscaled source occurrence offset. This is the precise failing coordinate-transform boundary: **source-leaf Location -> per-leaf scale**.

This is not a STEP exporter or Pattern 2 flattening failure:

- The in-memory external compound, flattened leaves, and re-imported failed STEP have the same external bounding boxes.
- The failed STEP faithfully serializes the already-wrong coordinates.
- The reference plate itself remains correctly mated because its imported `Location` is at the origin; a single plate mate cannot validate the other leaves.

## Floating External Leaves

The source asset contains 35 leaves. The mapper retains 32 source leaves (indices `0..34` excluding `11`, `14`, `18`) and adds two generated balance-axis replacements, yielding 34 external leaves in the failed STEP.

Use the local assembled functional band from the reference-plate lower face through the four primary escapement leaves:

```text
[-0.025000, 2.033183] mm in Z
```

### Entirely Below The Reference Plate: 17 Leaves

```text
external_escape_staff                    [-23.867804, -21.473889]
external_escapement_auxiliary_solid_06  [-16.361225, -16.267804]
external_escapement_auxiliary_solid_07  [-16.361225, -16.267804]
external_escapement_auxiliary_solid_08  [ -9.017804,  -8.924383]
external_escapement_auxiliary_solid_13  [ -9.017804,  -8.924383]
external_escapement_auxiliary_solid_16  [ -2.803906,  -2.336801]
external_escapement_auxiliary_solid_17  [ -2.803906,  -2.336801]
external_escapement_auxiliary_solid_24  [-16.314514, -16.267804]
external_escapement_auxiliary_solid_25  [-16.314514, -16.267804]
external_escapement_auxiliary_solid_26  [ -8.264514,  -8.217804]
external_escapement_auxiliary_solid_28  [ -9.017804,  -8.971093]
external_escapement_auxiliary_solid_29  [-19.355016, -19.092269]
external_escapement_auxiliary_solid_30  [-19.355016, -19.092269]
external_escapement_auxiliary_solid_31  [ -2.105016,  -1.842269]
external_escapement_auxiliary_solid_32  [ -2.105016,  -1.842269]
external_escapement_auxiliary_solid_33  [ -6.193339,  -5.930592]
external_escapement_auxiliary_solid_34  [ -6.193339,  -5.930592]
```

### Entirely Above The Active Escapement Core: 4 Leaves

```text
external_escape_upper_cap               [ 6.982196,  7.075617]
external_escape_upper_fixed_hardware    [13.196094, 13.663199]
external_escapement_auxiliary_solid_19  [ 6.055386,  7.982196]
external_escapement_auxiliary_solid_20  [ 8.055386,  9.982196]
```

Therefore, **21 of the 32 retained imported leaves are wholly outside the local Z assembly band**: 17 below and 4 above. A broader transform audit finds **23 retained leaves with a non-zero source `Location.Z` whose translation was not scaled**; the other two (`auxiliary_solid_21` and `_22`) stay inside the band only because their source Z offset is small.

The same defect also leaks unscaled XY occurrence offsets. For example, source leaf `6` retains source `Y=89.06` mm and exports near `Y=89.88` mm, rather than following the 0.058388 scale into the roughly 5 mm escapement region.

## Pattern 1 / Pattern 4 Control Comparison

Read-only controls:

```text
Pattern 1:
models/watch_kinematic/outputs/p1_seed_5908_complete_model/
  watch_power_chain_with_analytic_partitioned_bridges_and_scaled_swiss_lever_reference.step

Pattern 4:
models/watch_kinematic/outputs/pattern4_seed_731_gate_full/
  watch_power_chain_pattern4_independent_display_with_analytic_partitioned_bridges.step
```

Both control STEP files contain the same 34 external labels and show a coherent local external stack. Representative comparison:

```text
Occurrence                              Pattern 2 failed Z       Pattern 1 / 4 control Z
external_escape_staff                  [-23.868, -21.474]      [-0.469, 1.925]
external_escape_upper_cap              [  6.982,   7.076]      [ 1.333, 1.426]
external_escape_upper_fixed_hardware   [ 13.196,  13.663]      [ 1.426, 1.893]
external_auxiliary_solid_06            [-16.361, -16.268]      [-0.118,-0.025]
```

The controls have only two minor imported features just below the plate and no remote imported upper hardware; their generated balance upper-jewel bearing is deliberately at `Z=[4.230,4.330]` mm. The failed Pattern 2 artifact instead has the 21 remote imported leaves listed above.

The current source routes Pattern 1, Pattern 2, and Pattern 4 through the same `build_external_escapement_parts()` function. The normal control artifacts therefore demonstrate the required full-similarity result, but they do not prove that the current installed build123d runtime will reproduce it. The transform source has been stable in git since its original introduction; the most testable remaining explanation is a runtime/import transformation semantic difference rather than a Pattern 2-only exporter branch.

## Root-Cause Hypothesis And Falsifiable Test

### Hypothesis

The active build123d/OCP `Shape.scale()` implementation scales the leaf's underlying geometry but intentionally leaves `Shape.location` translation unchanged. The external source STEP is an assembly containing placed leaves. Applying this operation leaf-by-leaf therefore creates a mixed coordinate system: scaled geometry at unscaled occurrence locations. The Pattern 2 assembly and STEP exporter correctly preserve that malformed in-memory state.

### Minimal Test

Create an in-memory-only regression test against source leaf `6` using the failed seed's fit:

```text
raw_location = source_leaf[6].location.position
scaled_location = source_leaf[6].scale(fit.scale).location.position

assert scaled_location == fit.scale * raw_location
```

It fails now: raw and scaled locations are both `(0, 89.06, -17.25)` mm. A second assertion should compare a full transformed leaf occurrence against a reference constructed by applying the complete similarity transform to both geometry and placement. The acceptance condition is zero retained imported leaves with a placement residual greater than `0.01 mm`, followed by a post-export check that the 21 remote leaves no longer exist.

This report intentionally proposes no repair.
