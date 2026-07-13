from __future__ import annotations

import json
from pathlib import Path
import sys


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from models.watch_kinematic.watch_kinematic.external_escapement_replacement import (  # noqa: E402
    build_external_escapement_replacement,
)


CASE_DIR = WORKSPACE_ROOT / "models" / "watch_kinematic" / "outputs" / "power_chain_mvp_seed_123"


def main() -> None:
    result = build_external_escapement_replacement(CASE_DIR, seed=123)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
