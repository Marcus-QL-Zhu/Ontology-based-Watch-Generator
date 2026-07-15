# Computational Engineering Architecture

## Design Goal

The project turns reusable mechanical-design knowledge into executable assets:
design patterns, semantic role contracts, coupled constraints, geometry builders,
validators, and evidence reports. An agent can request a pattern and explore
different seeds, while deterministic code owns the engineering boundary and the
decision to publish.

This architecture is intentionally compatible with text-to-cad. Watch-specific
logic lives in the generator package. Shared STEP, topology, GLB, material,
motion, and CAD Explorer behavior remains in the reference text-to-cad backend.

## Two Technical Lineages

### Ontology For Generative Design

The ontology lineage answers: **what does each object mean in the design?**

The semantic evidence records:

- component roles and part-whole membership;
- interfaces, supports, and assembly relationships;
- power-chain membership and direction;
- material and visual intent;
- permitted degrees of freedom and motion bindings;
- validation requirements and proof fields.

This prevents a geometrically plausible object from silently losing its
engineering role. A shaft, bearing, bridge, gear, and decorative shape may look
similar in a viewer while requiring very different engineering contracts.

### Design Synthesis

The design-synthesis lineage answers: **how is a valid design found?**

Each public pattern declares a topology, variable domains, fixed interfaces, and
hard constraints. The generator solves a candidate, builds it, validates the
result, and rejects the attempt when a hard rule fails. A different seed can then
explore another region of the declared candidate space.

Ontology supplies meaning and evidence. Design synthesis supplies alternatives
and search. Their combination produces executable engineering semantics.

## Six-Layer System

### 1. Boundary Setup

The boundary fixes the case envelope, display topology, third-party interfaces,
selected pattern, and seed policy. It prevents the task definition from drifting
during generation.

### 2. Design-Pattern Synthesis

Patterns 1-3 represent different display and power-chain topologies. Each pattern
owns its candidate variables and topology-specific rules. The seed influences
selection inside allowed domains and never bypasses a hard constraint.

### 3. Semantic Sidecars

Sidecars describe roles, power chains, placement evidence, materials, motion,
kinematics, and validation results. They make engineering intent machine-readable
without trying to recover it later from STEP geometry or filenames.

### 4. Coupled Constraint Solving

The solver coordinates XY layout, Z-stack layers, gear ratios and phase, case
clearance, arbor and bearing envelopes, bridge partitioning, lightening windows,
and fastener service regions. Cross-layer checks prevent a locally valid XY or Z
result from being published when the complete assembly is inconsistent.

### 5. build123d Geometry Harness

The geometry harness uses build123d/OCP through controlled builder entry points.
Its reliability mechanisms include:

- local reference frames instead of fragile world-coordinate assumptions;
- stable labels and assembly occurrence identities;
- geometry generated downstream of solved topology and constraints;
- semantic material and motion contracts bound to those occurrences;
- the attributed escapement retained as a complete subassembly and placed through
  solved interfaces;
- one native text-to-cad artifact path for STEP, topology, GLB, and Explorer.

The harness avoids free-form part creation followed by visual guesswork. Geometry,
semantics, validation, and browser artifacts belong to the same generated run.

### 6. Validation And Atomic Publication

Each attempt runs in a private staging directory. Hard gates check required
artifacts, engineering reports, geometry envelopes, semantic coverage, materials,
motion bindings, and topology evidence. A passing package is moved atomically to
`current/`; a failed package is discarded before another distinct seed is tried.

`run-record.json` and `MANIFEST.json` preserve the successful seed, backend
entrypoint, artifact paths, and hashes so an accepted result can be reproduced
and audited.

## Semantic, Kinetic, And Dynamic Views

- **Semantic layer:** what components mean and how they relate.
- **Kinetic layer:** executable solvers, builders, artifact generation, and
  declared motion.
- **Dynamic layer:** validation feedback, failed-attempt isolation, retry, and
  retained evidence.

The current dynamic layer repairs at the candidate-attempt level. It does not yet
self-modify engineering rules or synthesize new topology families autonomously.

## Why The Harness Is Stable

1. The public command is thin and maps to one canonical pattern implementation.
2. Engineering constraints are solved before geometry is accepted.
3. Stable occurrence identities bind materials and motion to real assembly parts.
4. The same run produces geometry and its semantic evidence.
5. Hard failures stop publication rather than producing a partial success.
6. Seed retries are isolated and recorded.
7. Generated models stay outside version control; only source, tests, and the
   attributed non-regenerated escapement asset are distributed.

## Current Limits

The generator demonstrates bounded geometric and kinematic synthesis. It does not
certify:

- strength, fatigue, shock, wear, lubrication, or thermal performance;
- production tolerance stacks, metrology, or manufacturing processes;
- certified horological tooth forms or timing performance;
- complete AP242 assembly, PMI, tolerance, and mate semantics;
- global enumeration of every feasible design;
- winding and keyless works, automatic winding, calendars, or production
  detailing.

The Swiss-lever escapement is a modified and attributed third-party asset. Its
provenance and redistribution requirements are recorded in
[`THIRD_PARTY_ASSETS.md`](../../THIRD_PARTY_ASSETS.md).

## Extending Beyond Watches

A new design scenario should provide a complete vertical slice:

1. a bounded engineering brief;
2. one or more topology patterns;
3. role and interface contracts;
4. variable domains and coupled constraints;
5. deterministic geometry builders;
6. hard semantic, geometric, motion, and artifact validators;
7. evidence reports and parity tests;
8. a thin public adapter that reuses the native text-to-cad artifact pipeline.

This separation lets domain packages evolve independently while keeping reusable
CAD, renderer, and Explorer improvements easy to contribute upstream.
