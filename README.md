# Ontology-based Watch Generator

An open, parity-first mechanical watch generator built on a frozen, traceable `text-to-cad` reference backend. It publishes a complete engineering evidence chain alongside every generated STEP assembly: solver, semantic, role-contract, placement, motion, kinematic, validation, browser, and artifact-hash records.

## What is public

| Pattern | Display architecture | Public generator |
| --- | --- | --- |
| Pattern 1 | Central hour/minute, off-center seconds | `pattern-01` |
| Pattern 2 | Separate serial hour/minute, no seconds | `pattern-02` |
| Pattern 3 | Independent hour and minute branches, no seconds | `pattern-03` |

Pattern 3 is the public name for the accepted source Pattern 4 complete model. The source's legacy Pattern 3 is deliberately not part of this release.

## Quick start

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e .

ontology-watch generate pattern-01 --seed 731 --output $env:TEMP\ontology-watch-p1
```

The output directory receives an atomic `current/` folder. Its `run-record.json` and `MANIFEST.json` identify the backend entrypoint and SHA-256 hash every published artifact. The final STEP is accompanied by CAD Explorer data at `.<assembly.step>/model.glb`.

Run the fixed release matrix outside the checkout:

```powershell
python scripts\run_release_matrix.py
```

## Architecture

`reference_backend/` is a file-mapped frozen copy of the accepted source backend. It remains the only geometry, solver, material, motion, semantic, and validation implementation during this migration. Public Pattern adapters only call this backend and publish its native artifacts; they never rebuild geometry or infer semantics from STEP.

This makes an eventual upstream merge straightforward: the artifact envelope, public commands, and parity tests can move upstream while canonical CAD logic stays in its original `text-to-cad` modules. See [the upstream contribution map](docs/architecture/upstream-contribution-map.md), [migration boundary](docs/architecture/migration-boundary.md), and [source provenance](docs/provenance/text-to-cad-reference.md).

## Evidence and licensing

Each public generator uses the same-run, complete source orchestration. It fails closed if a required artifact or hard validation result is missing. Generated models are intentionally excluded from version control.

The Swiss-lever escapement is a separately preserved and modified third-party
asset. Its original author, GrabCAD source, exact hashes and project
modifications are documented in [THIRD_PARTY_ASSETS.md](THIRD_PARTY_ASSETS.md).
Keep that attribution with redistributed copies.

Development experiments must write into system temporary directories, never the source `text-to-cad` worktree.

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE).
