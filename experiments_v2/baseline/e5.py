from __future__ import annotations

import json
import re
from collections import Counter

from eval_utils import DATA, RESULTS, metrics, normalize, read_csv, write_csv

NUMBER_WORDS = {"बीस": 20, "पचास": 50, "सौ": 100, "वीस": 20, "पन्नास": 50, "शंभर": 100}
ITEM_ALIASES = {
    "चाय": "tea", "चहा": "tea", "कॉफी": "coffee", "केक": "cake",
    "साड़ी": "saree", "साडी": "saree", "फेशियल": "facial",
    "चार्जर": "charger",
}


def extract(text: str):
    pairs = []
    chunks = re.split(r"[,;]", text)
    for chunk in chunks:
        nums = re.findall(r"\d[\d,]*", chunk)
        price = int(nums[0].replace(",", "")) if nums else next((v for k, v in NUMBER_WORDS.items() if k in chunk), None)
        if price is None: continue
        item = re.sub(r"\d[\d,]*|रुपये|रुपया|rs|₹|बीस|पचास|सौ|वीस|पन्नास|शंभर", " ", chunk, flags=re.I)
        item = re.sub(r"\s+", " ", item).strip(" :-")
        if item: pairs.append([ITEM_ALIASES.get(item, item), price])
    return pairs


def main():
    out = RESULTS / "e5"; out.mkdir(parents=True, exist_ok=True)
    rows = read_csv(DATA / "price_lists.csv")
    try:
        result = []
        for row in rows:
            gold = json.loads(row["gold_pairs"]); predicted = extract(row["text"]); precision, recall, _ = metrics(gold, predicted)
            result.append({"id": row["id"], "style": row["style"], "precision": precision, "recall": recall, "exact_match": normalize(gold) == normalize(predicted), "predicted": json.dumps(predicted, ensure_ascii=False), "gold": row["gold_pairs"]})
            if int(row["id"]) <= 9:
                print(f"E5_TRACE function=extract id={row['id']} style={row['style']} raw={row['text']} parsed={predicted} gold={gold}")
        write_csv(out / "price_results.csv", result, list(result[0].keys()))
        summary = {style: {"n": sum(r["style"] == str(style) for r in result), "precision": sum(r["precision"] for r in result if r["style"] == str(style)) / max(1, sum(r["style"] == str(style) for r in result)), "recall": sum(r["recall"] for r in result if r["style"] == str(style)) / max(1, sum(r["style"] == str(style) for r in result)), "exact_match_rate": sum(r["exact_match"] for r in result if r["style"] == str(style)) / max(1, sum(r["style"] == str(style) for r in result))} for style in (1, 2, 3)}
        assert summary[1]["precision"] > 0, summary
        (out / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return {"status": "success", "n": len(rows), "failed": 0, "metrics": summary}
    except Exception as exc:
        (out / "error.txt").write_text(f"NOT RUN: {exc}", encoding="utf-8"); return {"status": "NOT RUN", "reason": str(exc), "n": 0, "failed": 0}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
