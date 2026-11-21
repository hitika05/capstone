from __future__ import annotations

import json
import re
from collections import Counter

from eval_utils import DATA, RESULTS, metrics, normalize, read_csv, write_csv

NUMBER_WORDS = {
    "शून्य": 0, "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9,
    "दस": 10, "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20, "पच्चीस": 25, "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90, "सौ": 100,
    "शंभर": 100, "वीस": 20, "पंचवीस": 25, "तीस": 30, "चाळीस": 40, "पन्नास": 50, "साठ": 60, "सत्तर": 70, "ऐंशी": 80, "नव्वद": 90,
}
ITEM_ALIASES = {
    "चाय": "tea", "चहा": "tea", "कॉफी": "coffee", "केक": "cake",
    "साड़ी": "saree", "साडी": "saree", "फेशियल": "facial",
    "चार्जर": "charger",
}
NUMBER_WORD_PATTERN = r"(?<![\w\u0900-\u097f])(?:" + "|".join(sorted(map(re.escape, NUMBER_WORDS), key=len, reverse=True)) + r")(?![\w\u0900-\u097f])"


def extract(text: str):
    pairs = []
    chunks = re.split(r"[,;]", text)
    for chunk in chunks:
        nums = re.findall(r"\d[\d,]*", chunk)
        word_match = re.search(NUMBER_WORD_PATTERN, chunk)
        price = int(nums[0].replace(",", "")) if nums else NUMBER_WORDS[word_match.group()] if word_match else None
        if price is None: continue
        item = re.sub(r"\d[\d,]*|रुपये|रुपया|रु|rs|₹|" + NUMBER_WORD_PATTERN, " ", chunk, flags=re.I)
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
