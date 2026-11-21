from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent / "backend"
sys.path.insert(0, str(BACKEND))
from services.pipeline_service import keyword_intent_parser
from e2 import accuracy


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parser_scores(rows, parser):
    fields = [("design_type", "design_type", lambda x: parser(x)["design_type"]),
              ("business_type", "business_type", lambda x: parser(x)["business"]),
              ("colors", "colors", lambda x: [parser(x)["color"]] if parser(x)["color"] else [])]
    result = {}
    for field, gold_field, predict in fields:
        result[field] = sum(accuracy(json.loads(r[gold_field]) if field == "colors" else r[gold_field], predict(r["command"]), field) for r in rows) / len(rows)
        majority = max(set(r[gold_field] for r in rows), key=lambda v: sum(x[gold_field] == v for x in rows))
        result[field + "_majority"] = sum(accuracy(json.loads(r[gold_field]) if field == "colors" else r[gold_field], json.loads(majority) if field == "colors" else majority, field) for r in rows) / len(rows)
    return result


def price_scores(rows, extractor):
    result = {}
    for style in (1, 2, 3):
        subset = [r for r in rows if int(r["style"]) == style]
        exact = 0
        for row in subset:
            gold = {tuple(pair) for pair in json.loads(row["gold_pairs"])}
            predicted = {tuple(pair) for pair in extractor(row["text"])}
            exact += gold == predicted
        result[str(style)] = {"n": len(subset), "exact_match_rate": exact / len(subset)}
    return result


def main():
    fresh = ROOT / "data_seed1"
    original = ROOT / "data"
    baseline_parser = load_module(ROOT / "baseline" / "pipeline_service.py", "baseline_pipeline")
    baseline_e5 = load_module(ROOT / "baseline" / "e5.py", "baseline_e5")
    current_e5 = load_module(ROOT / "e5.py", "current_e5")
    output = {"parser": {}, "price": {}, "errors": []}
    for label, data_dir in (("fresh_seed1_test", fresh), ("original_test_reference", original)):
        rows = [r for r in read(data_dir / "commands.csv") if r["split"] == "test"]
        output["parser"][label] = {
            "before": parser_scores(rows, baseline_parser.keyword_intent_parser),
            "after": parser_scores(rows, keyword_intent_parser),
        }
        prices = read(data_dir / "price_lists.csv")
        output["price"][label] = {"before": price_scores(prices, baseline_e5.extract), "after": price_scores(prices, current_e5.extract)}
        if label == "fresh_seed1_test":
            for row in rows:
                predicted = keyword_intent_parser(row["command"])
                gold = {"design_type": row["design_type"], "business_type": row["business_type"], "colors": json.loads(row["colors"])}
                actual = {"design_type": predicted["design_type"], "business_type": predicted["business"], "colors": [predicted["color"]] if predicted["color"] else []}
                for field in gold:
                    if not accuracy(gold[field], actual[field], field):
                        output["errors"].append({"id": row["id"], "field": field, "gold": gold[field], "predicted": actual[field]})
    (ROOT / "results" / "v2_eval.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
