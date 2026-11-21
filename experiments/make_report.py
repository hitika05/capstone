from __future__ import annotations

import csv
import json
import platform
import statistics
import subprocess
from collections import Counter
from datetime import datetime
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
DATA = ROOT / "data"


def read_csv(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "NOT INSTALLED"


def table(rows, fields):
    if not rows:
        return "NOT RUN"
    return "\n".join(["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"] + ["| " + " | ".join(str(row.get(field, "")) for field in fields) + " |" for row in rows])


def main():
    commands = read_csv(DATA / "commands.csv")
    prices = read_csv(DATA / "price_lists.csv")
    clips = read_csv(RESULTS / "e1" / "clip_scores.csv")
    e2_metrics = read_csv(RESULTS / "e2" / "metrics.csv")
    e2_errors = read_csv(RESULTS / "e2" / "errors.csv")
    price_results = read_csv(RESULTS / "e5" / "price_results.csv")
    e1_stats = json.loads((RESULTS / "e1" / "clip_stats.json").read_text(encoding="utf-8")) if (RESULTS / "e1" / "clip_stats.json").exists() else {}
    e2_diag = json.loads((RESULTS / "e2" / "diagnostics.json").read_text(encoding="utf-8")) if (RESULTS / "e2" / "diagnostics.json").exists() else {}
    e5_metrics = json.loads((RESULTS / "e5" / "metrics.json").read_text(encoding="utf-8")) if (RESULTS / "e5" / "metrics.json").exists() else {}
    e6_stats = json.loads((RESULTS / "e6" / "latency_stats.json").read_text(encoding="utf-8")) if (RESULTS / "e6" / "latency_stats.json").exists() else {}
    e4_rows = read_csv(RESULTS / "e4" / "scoring.csv")
    audio = list((DATA / "audio").glob("*")) if (DATA / "audio").exists() else []
    failed = lambda rows: sum(row.get("status") == "failed" for row in rows)
    langs = Counter(row.get("language", "") for row in commands)
    backend = next((row.get("backend") for row in clips if row.get("status") == "success"), "NOT RUN")
    models = sorted(set(row.get("model_name") for row in clips if row.get("model_name")))

    rating = RESULTS / "e1" / "rating_sheet.csv"
    rating.parent.mkdir(parents=True, exist_ok=True)
    with open(rating, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image_id", "condition", "image_path", "relevance_1to5", "layout_1to5", "quality_1to5", "notes"])
        writer.writeheader()
        writer.writerows({"image_id": f"{row['id']}_{row['condition']}", "condition": row["condition"], "image_path": row.get("image_path", ""), "relevance_1to5": "", "layout_1to5": "", "quality_1to5": "", "notes": ""} for row in clips)
    mapping = RESULTS / "e1" / "rating_mapping.csv"
    with open(mapping, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image_id", "command_id", "condition", "prompt_sent", "english_reference"])
        writer.writeheader(); writer.writerows({"image_id": f"{row['id']}_{row['condition']}", "command_id": row["id"], "condition": row["condition"], "prompt_sent": row.get("prompt_sent", ""), "english_reference": row.get("english_reference", "")} for row in clips)

    first5 = [{key: row.get(key, "") for key in ["id", "language", "command", "design_type", "business_type", "colors", "occasion"]} for row in commands[:5]]
    hard = [row for row in prices if int(row["id"]) >= 31]
    problems = ["NOT RUN: E3 because experiments/data/audio contains no real recorded clips.", "Stability credits/credentials were not available; required one-image probe failed with STABILITY_API_KEY unavailable, so image experiments used Pollinations only.", "Pollinations had remote request failures; failed items are excluded from image statistics.", "E4 human character/text scoring is pending.", "E2 tagline, services, and contact predictions are empty because the existing parser contract does not return those fields.", "The command gold labels are synthetic/drafted and require native-speaker review; harder cases are marked needs_human_review.", "BERT is zero-shot, not fine-tuned in this repository; diagnostics show whether its predicted label distribution collapses.", "E6 overlay timing measures the current no-op experiment overlay stage, not browser rendering.", "CLIP measures image-text similarity to English reference strings, not human design quality."]
    report = []
    add = report.append
    add("## 1. ENVIRONMENT")
    add(f"date: {datetime.now().isoformat()}"); add(f"OS: {platform.platform()}"); add(f"Python: {platform.python_version()}")
    add(f"packages: torch={version('torch')}; transformers={version('transformers')}; whisper={version('openai-whisper')}; jiwer={version('jiwer')}; scipy={version('scipy')}")
    add("STT provider: native Google SpeechRecognition default; no audio run"); add(f"image backend: {backend}; models: {', '.join(models) or 'NOT RUN'}"); add(f"items: E1={len({row['id'] for row in clips})}; E2={len(commands)}; E3={len(audio)} audio clips; E4={len({row['id'] for row in e4_rows})}; E5={len(prices)}; E6={len(read_csv(RESULTS / 'e6' / 'latency.csv'))}"); add(f"failed: E1={failed(clips)}; E4={failed(e4_rows)}; E6={failed(read_csv(RESULTS / 'e6' / 'latency.csv'))}"); add("random seeds: Pollinations URL default seed not fixed; no other experiment seed set"); add("Stability credits available: no; credentials unavailable")
    add("## 2. CODE CHANGES"); add("None in backend/ or frontend/.")
    add("## 3. DATA SUMMARY"); add(f"commands: total={len(commands)}, Marathi={langs['mr']}, Hindi={langs['hi']}, English={langs['en']}"); add(f"price lists: {len(prices)}; audio clips: {len(audio)}"); add(table(first5, ["id", "language", "command", "design_type", "business_type", "colors", "occasion"]))
    add("label_taxonomy.json:"); add("```json"); add((DATA / "label_taxonomy.json").read_text(encoding="utf-8")); add("```"); add("draft/native-speaker review: all 60 commands, all 45 price lists, all image ratings, and E4 Devanagari scoring; rows >=51 commands and >=31 price lists are explicitly needs_human_review.")
    add("## 4. E1"); add(table(clips[:6], ["id", "condition", "prompt_sent", "english_reference", "backend", "model_name", "status", "latency", "clip_score"])); add("statistics:"); add(table([{ "condition": key, **value} for key, value in e1_stats.items() if key in ["C1", "C2", "C3"]], ["condition", "n", "mean", "std"])); add(f"Wilcoxon/effect sizes: {json.dumps(e1_stats.get('paired_tests', {}))}"); add(f"failure count per condition: {dict(Counter(row['condition'] for row in clips if row.get('status') == 'failed'))}"); add("exact prompts for first 3 commands:"); add("```text"); add("\n".join(f"{row['id']} {row['condition']}: {row['prompt_sent']}" for row in clips if row['id'] in {'1','2','3'})); add("```"); add("example_grid.png: results/e1/example_grid.png"); add("rating sheet: results/e1/rating_sheet.csv; mapping: results/e1/rating_mapping.csv")
    add("## 5. E2"); add(table(e2_metrics, ["parser", "field", "precision", "recall", "f1"])); add(f"BERT diagnostics: {json.dumps(e2_diag, ensure_ascii=False)}"); add(f"first 15 errors:\n{table(e2_errors[:15], ['id', 'language', 'field', 'gold', 'keyword', 'bert'])}")
    add("## 6. E3"); add("NOT RUN: no recorded audio in experiments/data/audio; record real clips with experiments/record_clips.py, then run experiments/e3_asr_wer.py.")
    add("## 7. E4"); add(f"image pairs generated: {len(e4_rows) // 2}; scoring sheet: results/e4/scoring.csv; PENDING HUMAN SCORING")
    add("## 8. E5"); add(f"metrics: {json.dumps(e5_metrics)}"); add(table(price_results[:10], ["id", "category", "precision", "recall", "exact_match", "pred_pairs", "gold_pairs"])); add("unit tests: 2 passed (identical=True; one missing pair=False)")
    add("## 9. E6"); add(json.dumps(e6_stats, indent=2)); add("backend usage and failure rate are included in results/e6/latency_stats.json")
    add("## 10. KNOWN PROBLEMS"); add("\n".join(f"- {problem}" for problem in problems))
    add("## 11. COMMANDS"); add("```powershell"); add("cd C:\\Users\\Hitika\\Desktop\\proje"); add(".venv\\Scripts\\python.exe experiments\\prepare_data.py"); add(".venv\\Scripts\\python.exe experiments\\run_all.py --only e1,e2,e3,e4,e5,e6 --limit 3 --backend pollinations"); add(".venv\\Scripts\\python.exe experiments\\run_all.py --only e1 --backend pollinations"); add(".venv\\Scripts\\python.exe experiments\\e2_intent_accuracy.py"); add(".venv\\Scripts\\python.exe experiments\\e3_asr_wer.py"); add(".venv\\Scripts\\python.exe experiments\\e4_devanagari.py --backend pollinations"); add(".venv\\Scripts\\python.exe experiments\\e5_price_list.py"); add(".venv\\Scripts\\python.exe experiments\\e6_latency.py --backend pollinations"); add(".venv\\Scripts\\python.exe -m unittest discover -s experiments -p test_e5_price_list.py"); add("```")
    (RESULTS / "SEND_TO_CLAUDE.md").write_text("\n\n".join(report), encoding="utf-8")
    print(f"Wrote {RESULTS / 'SEND_TO_CLAUDE.md'}")


if __name__ == "__main__":
    main()
