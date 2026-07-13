# Contributing

## Development boundary

`src/ontology_watch_generator/reference_backend/` is a mapped, frozen copy of the accepted `text-to-cad` backend. Do not edit it directly. Changes to geometry, solvers, materials, motion, or validation belong upstream first, then the source map and parity baselines are deliberately refreshed.

New repository code belongs in adapters, artifact publication, documentation, or tests. A contribution must not reconstruct CAD geometry or sidecars from STEP output.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e .
ontology-watch generate pattern-01 --seed 731 --output $env:TEMP\ontology-watch-p1
```

Always write generated artifacts outside this checkout. The publisher creates `<output>/current/` atomically.

## Before a pull request

```powershell
python scripts/verify_reference_backend.py
python -m pytest -q
python scripts/run_release_matrix.py
```

Changes affecting public generation require a fresh baseline/parity review and must preserve the complete evidence chain: solver, semantic, role-contract, placement, motion, kinematic, validation, model, and browser artifacts.
