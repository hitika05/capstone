from __future__ import annotations

import json
from pathlib import Path

from eval_utils import RESULTS


def main():
    out = RESULTS / "e4"; out.mkdir(parents=True, exist_ok=True)
    reason = "overlay is in the frontend: frontend/src/components/DesignViewer.jsx and frontend/src/App.jsx; no real backend Python overlay exists"
    (out / "status.txt").write_text(f"NOT RUN: {reason}", encoding="utf-8")
    return {"status": "NOT RUN", "reason": reason, "n": 0, "failed": 0}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
