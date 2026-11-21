#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = ROOT.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.pipeline_service import DESIGN_TYPES, keyword_intent_parser

RESULTS_DIR = ROOT / "results" / "e2"
TAXONOMY = ROOT / "data" / "label_taxonomy.json"


def f1_for(gold, predicted, field: str) -> dict:
    gold_set = set(gold if isinstance(gold, list) else ([gold] if gold else []))
    predicted_set = set(predicted if isinstance(predicted, list) else ([predicted] if predicted else []))
    true_positive = len(gold_set & predicted_set)
    precision = true_positive / len(predicted_set) if predicted_set else 0.0
    recall = true_positive / len(gold_set) if gold_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"field": field, "precision": precision, "recall": recall, "f1": f1}


def load_bert_once():
    model_id = os.getenv("INTENT_MODEL_ID", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
    try:
        from transformers import pipeline
        classifier = pipeline("zero-shot-classification", model=model_id)
        return classifier, model_id, "zero-shot head loaded from checkpoint", "unknown"
    except Exception as exc:
        return None, model_id, f"NOT RUN: {exc}", "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ROOT / "data" / "commands.csv", "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if args.limit is not None:
        rows = rows[: args.limit]
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    classifier, checkpoint, head_status, trained_examples = load_bert_once()
    predictions = []
    errors = []
    label_distribution = Counter()

    for row in rows:
        text = row["command"]
        keyword = keyword_intent_parser(text)
        if classifier is None:
            bert = {"design_type": "NOT RUN", "business": "", "color": ""}
        else:
            bert = keyword.copy()
            result = classifier(text, DESIGN_TYPES)
            bert["design_type"] = result["labels"][0] if result.get("labels") else ""
            label_distribution[bert["design_type"]] += 1
        gold = {
            "design_type": row["design_type"],
            "business_type": row["business_type"],
            "colors": [item.strip() for item in row["colors"].split(",") if item.strip() and item.strip() != "needs_human_review"],
            "tagline": row["tagline"] if row["tagline"] != "needs_human_review" else "",
            "services": [item.strip() for item in row["services"].split(",") if item.strip()],
            "contact": row["contact"] if row["contact"] != "needs_human_review" else "",
        }
        pred_keyword = {"design_type": keyword.get("design_type", ""), "business_type": keyword.get("business", ""), "colors": [keyword.get("color", "")] if keyword.get("color") else [], "tagline": "", "services": [], "contact": ""}
        pred_bert = {**pred_keyword, "design_type": bert.get("design_type", ""), "business_type": bert.get("business", ""), "colors": [bert.get("color", "")] if bert.get("color") else []}
        predictions.append({"id": row["id"], "keyword": pred_keyword, "bert": pred_bert, "gold": gold, "language": row["language"], "command": text})
        errors.append({"id": row["id"], "language": row["language"], "field": "design_type", "gold": gold["design_type"], "keyword": pred_keyword["design_type"], "bert": pred_bert["design_type"]})

    metrics = []
    for parser_name in ("keyword", "bert"):
        for field in ("design_type", "business_type", "colors", "tagline", "services", "contact"):
            per_item = [f1_for(item["gold"][field], item[parser_name][field], field) for item in predictions]
            metrics.append({"parser": parser_name, "field": field, **{key: sum(item[key] for item in per_item) / len(per_item) if per_item else 0.0 for key in ("precision", "recall", "f1")}})

    with open(RESULTS_DIR / "metrics.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["parser", "field", "precision", "recall", "f1"])
        writer.writeheader(); writer.writerows(metrics)
    with open(RESULTS_DIR / "errors.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "language", "field", "gold", "keyword", "bert"])
        writer.writeheader(); writer.writerows(errors)
    (RESULTS_DIR / "diagnostics.json").write_text(json.dumps({"checkpoint": checkpoint, "label_list": DESIGN_TYPES, "classification_head": head_status, "trained_examples": trained_examples, "predicted_label_distribution": dict(label_distribution), "taxonomy_path": str(TAXONOMY), "taxonomy_loaded": bool(taxonomy)}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved E2 metrics, diagnostics, and errors to {RESULTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
