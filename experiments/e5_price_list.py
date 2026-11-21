#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results" / "e5"

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "बीस": 20, "पन्नास": 50, "सौ": 100, "दोन": 2, "तीन": 3, "चार": 4, "पाच": 5, "पन्नास": 50, "पंधराशे": 1500, "दोन हजार चारशे": 2400, "आठशे": 800,
    "पचास": 50, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90, "तीन सौ": 300, "छह सौ": 600, "दो सौ": 200, "आठ सौ": 800,
}


def normalize_pair(pair) -> tuple:
    item, price = pair
    item = unicodedata.normalize("NFC", str(item)).strip().lower()
    if isinstance(price, list):
        price_value = tuple(int(value) for value in price)
    else:
        price_value = int(price)
    return item, price_value


def normalize_pairs(pairs) -> list[tuple]:
    return sorted(Counter(normalize_pair(pair) for pair in pairs).elements())


def number_value(text: str):
    digits = re.findall(r"\d[\d,]*", text)
    if digits:
        return int(digits[0].replace(",", ""))
    for phrase, value in sorted(NUMBER_WORDS.items(), key=lambda item: len(item[0]), reverse=True):
        if phrase in text.lower():
            return value
    return None


def parse_pairs(text: str):
    pairs = []
    for chunk in re.split(r"[,;]|\band\b| और | आणि | तथा | तसेच ", text, flags=re.IGNORECASE):
        chunk = chunk.strip()
        if not chunk:
            continue
        range_numbers = re.findall(r"(\d[\d,]*)\s*(?:ते|से|to|-)\s*(\d[\d,]*)", chunk, flags=re.IGNORECASE)
        if range_numbers:
            price = [int(range_numbers[0][0].replace(",", "")), int(range_numbers[0][1].replace(",", ""))]
        else:
            price = number_value(chunk)
        if price is None:
            continue
        item = re.sub(r"\d[\d,]*|रुपये|रुपया|रुपय|rs\.?|₹|only|at|की price|की कीमत|ची किंमत|फक्त|starting|for|is|है|आहे", " ", chunk, flags=re.IGNORECASE)
        for phrase in NUMBER_WORDS:
            item = item.replace(phrase, " ")
        item = re.sub(r"\s+", " ", item).strip(" -:")
        if item:
            pairs.append((item, price))
    return pairs


def score(gold, predicted) -> tuple[int, int, int]:
    gold_counter = Counter(normalize_pairs(gold))
    pred_counter = Counter(normalize_pairs(predicted))
    true_positive = sum((gold_counter & pred_counter).values())
    return true_positive, sum(pred_counter.values()), sum(gold_counter.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ROOT / "data" / "price_lists.csv", "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if args.limit is not None:
        rows = rows[: args.limit]
    output = []
    totals = {"original": [0, 0, 0], "harder": [0, 0, 0]}
    for row in rows:
        gold = json.loads(row["gold_pairs_json"])
        predicted = parse_pairs(row["text"])
        tp, pred_count, gold_count = score(gold, predicted)
        category = "harder" if int(row["id"]) >= 31 else "original"
        for index, value in enumerate((tp, pred_count, gold_count)):
            totals[category][index] += value
        output.append({"id": row["id"], "language": row["language"], "category": category, "pred_count": pred_count, "gold_count": gold_count, "true_positive": tp, "precision": tp / pred_count if pred_count else 0.0, "recall": tp / gold_count if gold_count else 0.0, "exact_match": normalize_pairs(predicted) == normalize_pairs(gold), "pred_pairs": json.dumps(predicted, ensure_ascii=False), "gold_pairs": row["gold_pairs_json"], "review_status": row.get("review_status", "")})
    with open(RESULTS_DIR / "price_results.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0].keys()) if output else ["id"])
        writer.writeheader(); writer.writerows(output)
    summary = {}
    for category, (tp, pred_count, gold_count) in totals.items():
        summary[category] = {"precision": tp / pred_count if pred_count else 0.0, "recall": tp / gold_count if gold_count else 0.0, "exact_match_rate": sum(row["exact_match"] for row in output if row["category"] == category) / max(1, sum(row["category"] == category for row in output))}
    (RESULTS_DIR / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved E5 results and metrics to {RESULTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
