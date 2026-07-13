# Watch Pattern Card Source Map

This folder contains executable watch pattern-card packages. Use it as source code, not as generated evidence.

Before editing a pattern, read the standalone project's public pattern map and
package documentation. Do not depend on a machine-local source worktree.

Package convention:

- `card.py` declares the role contract, hard constraints, negative cases, and markdown/json card writer.
- `solver.py` owns the deterministic or seeded layout solver and must emit explicit proof fields for hard constraints.
- `review.py` writes human-readable 2D review pages only; it must not become the source of engineering truth.
- `__init__.py` exports the package entry points.

Validation rule:

- Add or update tests before changing solver contracts, hard gates, bridge service rules, motion semantics, or package IDs.
- Do not put one-off generated STEP/HTML/PNG artifacts in this source folder.
- If a pattern needs a compatibility facade, keep the facade thin and point back to the package.
- Pattern 4's complete-model entry is a deliverable path: it must default to lightened bridges. Use `include_lightening=False` only for targeted debug or speed tests.
