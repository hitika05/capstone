from __future__ import annotations

import csv
import json
import platform
import statistics
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent; DATA = ROOT / "data"; RESULTS = ROOT / "results"

def version(name):
    try: return metadata.version(name)
    except metadata.PackageNotFoundError: return "NOT INSTALLED"

def rows(path):
    if not path.exists(): return []
    with open(path, encoding="utf-8", newline="") as h: return list(csv.DictReader(h))

def md_table(items, fields):
    if not items: return "NOT RUN"
    return "| " + " | ".join(fields) + " |\n|" + "|".join("---" for _ in fields) + "|\n" + "\n".join("| " + " | ".join(str(item.get(f, "")) for f in fields) + " |" for item in items)

def status(exp):
    error = RESULTS / exp / "error.txt"
    if error.exists(): return error.read_text(encoding="utf-8").strip()
    status_file = RESULTS / exp / "status.txt"
    if status_file.exists(): return status_file.read_text(encoding="utf-8").strip()
    return "completed"

def runner_status(run_log, script):
    item = next((row for row in run_log if row.get("script") == script), None)
    if not item: return "NOT RUN: no runner record"
    if item.get("returncode") == -2: return item.get("stderr", "NOT RUN: timeout")
    if item.get("returncode") != 0: return item.get("stderr", "NOT RUN: nonzero exit")
    return "completed"

def main():
    commands = rows(DATA / "commands.csv"); prices = rows(DATA / "price_lists.csv")
    e1 = rows(RESULTS / "e1" / "clip_scores.csv"); e2 = rows(RESULTS / "e2" / "metrics.csv"); e2_errors = rows(RESULTS / "e2" / "errors.csv"); e5 = rows(RESULTS / "e5" / "price_results.csv")
    e1_stats = json.loads((RESULTS / "e1" / "stats.json").read_text()) if (RESULTS / "e1" / "stats.json").exists() else {}
    e2_diag = json.loads((RESULTS / "e2" / "diagnostics.json").read_text()) if (RESULTS / "e2" / "diagnostics.json").exists() else {}
    e5_stats = json.loads((RESULTS / "e5" / "metrics.json").read_text()) if (RESULTS / "e5" / "metrics.json").exists() else {}
    e6_stats = json.loads((RESULTS / "e6" / "stats.json").read_text()) if (RESULTS / "e6" / "stats.json").exists() else {}
    run_log = json.loads((RESULTS / "run_log.json").read_text()) if (RESULTS / "run_log.json").exists() else []
    env = json.loads((RESULTS / "e1" / "timing_probe.json").read_text()) if (RESULTS / "e1" / "timing_probe.json").exists() else {}
    lines = []
    add = lines.append
    add("## ENVIRONMENT"); add(f"date: {__import__('datetime').datetime.now().isoformat()}"); add(f"OS: {platform.platform()}"); add(f"Python: {platform.python_version()}"); add(f"torch: {version('torch')}; CUDA: {env.get('environment', {}).get('cuda', 'NOT RUN')}; model: {env.get('environment', {}).get('model', 'NOT RUN')}; hardware: {env.get('environment', {}).get('gpu', 'NOT RUN')}"); add("seed: 0 for data/statistics; image seed=1000+command id; price/data generation uses seed 0"); add("external image services: never used")
    add("## CODE CHANGES"); add("None in backend/ or frontend/.")
    add("## DATA"); add(f"commands={len(commands)}; Hindi={sum(r['language']=='hi' for r in commands)}; Marathi={sum(r['language']=='mr' for r in commands)}; dev={sum(r['split']=='dev' for r in commands)}; test={sum(r['split']=='test' for r in commands)}; price_lists={len(prices)}")
    add("## E1 IMAGE ABLATION"); add(f"status: {status('e1')}; test_items={len(set(r['id'] for r in e1))}; rows={len(e1)}; failed={sum(r.get('status')=='failed' for r in e1)}"); add(f"stats: {json.dumps(e1_stats, ensure_ascii=False)}"); add("example_grid.png: NOT RUN: local diffusers model unavailable")
    e2_status = "completed" if e2 else runner_status(run_log, "e2.py")
    e2_report_rows = [r for r in e2 if r["split"] in {"dev", "test"} and r["field"] in {"design_type", "business_type", "colors"}]
    add("## E2 PARSER"); add("Review/Edit parser: keyword_intent_parser called directly; no BERT/mDeBERTa model loaded."); add(f"status: {e2_status}; rows={len(commands) if e2 else 0}"); add(md_table(e2_report_rows, ["split", "parser", "field", "precision", "recall", "f1"])); add("Other parser fields mood, action, parser_mode: NOT APPLICABLE (no gold labels)."); add("10 example errors:"); add(md_table(e2_errors[:10], ["id", "split", "field", "gold", "predicted"])); add(f"diagnostics: {json.dumps(e2_diag, ensure_ascii=False)}"); add("errors.csv: results/e2/errors.csv")
    add("## E3 SPEECH"); add(runner_status(run_log, "e3.py")); add("Audio label if run: synthetic TTS speech, clean, an upper bound.")
    add("## E4 DEVANAGARI"); add(status("e4")); add("Scoring: approximate, OCR-based only if backend overlay exists; current app overlay is frontend-owned.")
    e5_status = "completed" if e5 else runner_status(run_log, "e5.py")
    add("## E5 PRICE LISTS"); add(f"status: {e5_status}; rows={len(e5)}"); add(f"metrics: {json.dumps(e5_stats, ensure_ascii=False)}"); add(md_table(e5[:6], ["id", "style", "precision", "recall", "exact_match"])); add("Trace: e5.py prints the called function, raw input, parsed pairs, and gold pairs for the first 3 inputs of each style.")
    add("## E6 LATENCY"); add(f"status: {status('e6')}; runs={len(json.loads((RESULTS/'e6'/'latency.json').read_text())) if (RESULTS/'e6'/'latency.json').exists() else 0}; stats: {json.dumps(e6_stats, ensure_ascii=False)}")
    isolation_failures = [{"script": row.get("script"), "returncode": row.get("returncode"), "stderr": row.get("stderr", "")} for row in run_log if row.get("returncode") != 0 and not (row.get("script") == "e2.py" and e2)]
    add("## KNOWN PROBLEMS"); add("- No diffusers package is installed in the current environment, so local SD-Turbo/SDXL image generation is NOT RUN and no placeholder images are substituted."); add("- No faster-whisper package is installed; gTTS and Google SpeechRecognition require external network services and are isolated/reported as NOT RUN on failure."); add("- EasyOCR is not installed; E4 is NOT RUN because the real overlay is in the frontend."); add("- The app's BERT parser is zero-shot and loads its model inside the existing function; it is labeled zero-shot, not trained."); add("- Generated gold labels are programmatic by construction, not human-validated natural-language annotations."); add(f"- current runner isolation failures: {json.dumps(isolation_failures, ensure_ascii=False)}")
    add("## COMMANDS"); add("data_gen.py, e2.py, e5.py, and report.py run with .venv\\Scripts\\python.exe")
    assert len(lines) <= 100
    report = "\n".join(lines)
    assert len(report.splitlines()) <= 100
    (RESULTS / "SEND_TO_CLAUDE.md").write_text(report, encoding="utf-8")
    print(RESULTS / "SEND_TO_CLAUDE.md")

if __name__ == "__main__": main()
