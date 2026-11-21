from __future__ import annotations

import csv
import json
import sys
from collections import Counter

from eval_utils import DATA, RESULTS, metrics, read_csv, write_csv

PARSER_FIELDS = ["design_type", "business", "color", "mood", "action", "parser_mode"]


def canonical_business(value):
    groups = {
        "bakery": ["bakery", "cake shop", "बेकरी", "केक शॉप"],
        "tailor shop": ["tailor", "tailoring", "sewing", "दर्जी", "टेलर", "सिलाई", "शिंपी"],
        "beauty salon": ["salon", "beauty parlour", "beauty salon", "पार्लर", "सैलून", "ब्यूटी"],
        "mobile shop": ["mobile shop", "mobile repair", "phone shop", "मोबाइल", "मोबाईल"],
        "saree shop": ["saree", "sari", "साड़ी", "साडी", "boutique"],
        "grocery": ["grocery", "किराना", "किराणा", "ग्रॉसरी"],
        "chai stall": ["chai stall", "चाय", "चहा"],
        "sweet shop": ["sweet shop", "sweets", "मिठाई"],
        "jewelry": ["jewelry", "jewellery", "ज्वेलरी", "ज्वेलर्स", "सोनार"],
        "electronics": ["electronics", "इलेक्ट्रॉनिक्स"],
        "flower shop": ["flower shop", "flowers", "फूल", "फुले", "फुलांचे", "फुलवाला"],
        "yoga studio": ["yoga studio", "योग", "योगा", "योग स्टूडियो", "योग स्टुडिओ"],
    }
    value = str(value or "").strip().lower()
    return next((label for label, aliases in groups.items() if value in aliases), value)


def canonical_colors(value):
    aliases = {
        "नीला": "blue", "निळा": "blue", "लाल": "red", "हरा": "green", "हिरवा": "green",
        "गुलाबी": "pink", "सुनहरा": "gold", "सोनेरी": "gold", "सफेद": "white", "पांढरा": "white",
        "बैंगनी": "purple", "जांभळा": "purple", "नारंगी": "orange",
    }
    return {aliases.get(str(item).strip().lower(), str(item).strip().lower()) for item in (value or [])}


def accuracy(gold_value, predicted_value, field):
    if field == "business_type":
        return canonical_business(gold_value) == canonical_business(predicted_value)
    if field == "colors":
        return canonical_colors(gold_value) == canonical_colors(predicted_value)
    return str(gold_value or "").strip().lower() == str(predicted_value or "").strip().lower()


def gold(row):
    return {"design_type": row["design_type"], "business_type": row["business_type"], "colors": json.loads(row["colors"]), "occasion": row["occasion"], "shop_name": row["shop_name"], "services": json.loads(row["services"]), "contact": row["contact"]}


def main():
    out = RESULTS / "e2"; out.mkdir(parents=True, exist_ok=True)
    rows = read_csv(DATA / "commands.csv")
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        backend = str(DATA.parent.parent / "backend")
        if backend not in sys.path: sys.path.insert(0, backend)
        from services.pipeline_service import keyword_intent_parser

        predictions = []
        for row in rows:
            predictions.append({"id": row["id"], "split": row["split"], "gold": gold(row), "parser": keyword_intent_parser(row["command"]), "command": row["command"]})

        metric_rows = []
        for split in ("dev", "test", "all"):
            subset = predictions if split == "all" else [p for p in predictions if p["split"] == split]
            for field, gold_field, predicted in [
                ("design_type", "design_type", lambda p: p["parser"]["design_type"]),
                ("business_type", "business_type", lambda p: p["parser"]["business"]),
                ("colors", "colors", lambda p: [p["parser"]["color"]] if p["parser"]["color"] else []),
            ]:
                score = sum(accuracy(p["gold"][gold_field], predicted(p), field) for p in subset) / len(subset)
                metric_rows.append({"split": split, "parser": "keyword", "field": field, "accuracy": score})
            for field in ["mood", "action", "parser_mode"]:
                metric_rows.append({"split": split, "parser": "keyword", "field": field, "accuracy": "NOT APPLICABLE"})
            for field, gold_field in [("design_type", "design_type"), ("business_type", "business_type")]:
                values = [p["gold"][gold_field] for p in subset]
                majority = Counter(values).most_common(1)[0][0]
                score = sum(accuracy(p["gold"][gold_field], majority, field) for p in subset) / len(subset)
                metric_rows.append({"split": split, "parser": "majority_baseline", "field": field, "accuracy": score})
        write_csv(out / "metrics.csv", metric_rows, ["split", "parser", "field", "accuracy"])
        errors = []
        for p in predictions:
            for field, gold_field, predicted in [
                ("design_type", "design_type", p["parser"]["design_type"]),
                ("business_type", "business_type", p["parser"]["business"]),
                ("colors", "colors", [p["parser"]["color"]] if p["parser"]["color"] else []),
            ]:
                if not accuracy(p["gold"][gold_field], predicted, field):
                    errors.append({"id": p["id"], "split": p["split"], "field": field, "gold": json.dumps(p["gold"][gold_field], ensure_ascii=False), "predicted": json.dumps(predicted, ensure_ascii=False)})
        write_csv(out / "errors.csv", errors, ["id", "split", "field", "gold", "predicted"])
        diagnostics = {"review_edit_function": "backend.services.pipeline_service.keyword_intent_parser via parse_intent(text, mode='review')", "bert_status": "NOT RUN by design; E2 directly evaluates keyword_intent_parser", "parser_fields": PARSER_FIELDS, "taxonomy_written_before_run": True}
        (out / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"status": "success", "n": len(rows), "failed": 0, "metrics": str(out / "metrics.csv")}
    except Exception as exc:
        (out / "error.txt").write_text(f"NOT RUN: {exc}", encoding="utf-8"); return {"status": "NOT RUN", "reason": str(exc), "n": 0, "failed": 0}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
