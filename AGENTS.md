# Agent Workflow

When asked to generate a watch model, use `scripts/generate_and_open.py`.

- Accept a user seed or let the script choose one. If a source gate fails, retry with a new seed up to the configured limit.
- Treat the final STEP paired with `.<step-name>/model.glb` as the deliverable.
- Open the printed CAD Explorer URL in the in-app browser. A dashboard is supporting evidence, never a substitute for the model.
- Perform a visual self-check in CAD Explorer before asking the user to review it.
- If every attempt fails or CAD Explorer is unavailable, report the blocker instead of presenting a dashboard as success.
