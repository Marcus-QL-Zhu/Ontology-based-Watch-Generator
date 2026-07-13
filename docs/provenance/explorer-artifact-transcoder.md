# Explorer Artifact Transcoder Provenance

The public generator publishes a browser-ready GLB as a **derived artifact** of the same-run final STEP. This converter does not inspect or alter the design solver, CAD geometry, semantic sidecars, or motion sidecars.

The implementation under `src/ontology_watch_generator/integrations/text_to_cad/explorer_artifacts/` was imported from the generic CAD Explorer conversion utilities at the frozen `text-to-cad` source commit `5be7852844a3f4c5698a737eba81c026e96ced16`. Import statements and output-path helpers were locally rebased so the standalone package has no source-worktree dependency.

| Imported source file | Frozen SHA-256 | Local role |
| --- | --- | --- |
| `.agents/skills/cad/scripts/common/glb.py` | `6c160200569911331bebe020eb17ee07ad9515976ed1f63bf7f14e85caf806f1` | GLB writer and topology extension |
| `.agents/skills/cad/scripts/common/glb_mesh_payload.py` | `562ad7e4af220914742641f589e0876139ba927aa759e1a0a6377dccc65520e0` | OpenCascade mesh payload extraction |
| `.agents/skills/cad/scripts/common/step_scene.py` | `505e6d17bf96602227a68b58e4802bc146ffae3423d4166a0a84da2bc6dc8fd5` | STEP assembly/XCAF reader and selector extraction |
| `.agents/skills/cad/scripts/common/selector_types.py` | `4b486504a54c5c65b4784d57539e97caaeae2fb6934b50b3f5af8e2411c9f93e` | Selector artifact types |

For a final `assembly.step`, the derived artifact is emitted at `.assembly.step/model.glb` and is included in `run-record.json` and `MANIFEST.json` with its SHA-256. This is intentionally distinct from the frozen watch `reference_backend`: it is reusable browser infrastructure, not watch-domain design logic.
