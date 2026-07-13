# Immutable Artifact Envelope

Public generation adapters may publish a completed reference run, but may not solve, edit, or regenerate its geometry. A `RunRecord` identifies the requested and resolved seed, frozen source commit, backend entrypoint, design identifier, and exact required artifact filenames.

The publisher copies only the declared artifacts into a private staging directory, writes `run-record.json` and `MANIFEST.json` with SHA-256 values, then atomically replaces `current/`. Missing required artifacts, a seed mismatch, or an extra semantic or motion sidecar blocks publication.
