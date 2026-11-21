from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ["e1.py", "e2.py", "e3.py", "e4.py", "e5.py", "e6.py"]


def run(script):
    try:
        process = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, capture_output=True, text=True, timeout=300)
        return {"script": script, "returncode": process.returncode, "stdout": process.stdout[-4000:], "stderr": process.stderr[-4000:]}
    except subprocess.TimeoutExpired:
        return {"script": script, "returncode": -2, "stdout": "", "stderr": "NOT RUN: experiment exceeded 300 second isolation timeout"}
    except Exception as exc:
        return {"script": script, "returncode": -1, "stdout": "", "stderr": f"NOT RUN: {exc}"}


def main():
    subprocess.run([sys.executable, str(ROOT / "data_gen.py")], cwd=ROOT, check=True)
    results = [run(script) for script in SCRIPTS]
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "run_log.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "report.py")], cwd=ROOT, check=False)
    print(ROOT / "results" / "SEND_TO_CLAUDE.md")


if __name__ == "__main__": main()
