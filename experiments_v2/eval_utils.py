from __future__ import annotations

import csv
import json
import math
import random
import statistics
import unicodedata
from pathlib import Path
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
SEED = 0


def read_csv(path: Path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def parse_json_field(value: str):
    try: return json.loads(value)
    except Exception: return []


def normalize(value):
    if isinstance(value, list): return tuple(normalize(x) for x in value)
    if isinstance(value, int): return value
    return unicodedata.normalize("NFC", str(value or "")).strip().lower()


def metrics(gold, predicted):
    g = set(normalize(gold) if isinstance(gold, list) else [normalize(gold)] if gold not in (None, "") else [])
    p = set(normalize(predicted) if isinstance(predicted, list) else [normalize(predicted)] if predicted not in (None, "") else [])
    tp = len(g & p); precision = tp / len(p) if p else 0.0; recall = tp / len(g) if g else 0.0
    return precision, recall, 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def safe_number(value):
    try:
        number = float(value); return number if math.isfinite(number) else None
    except Exception: return None


def summarize(values):
    clean = [safe_number(v) for v in values]; clean = [v for v in clean if v is not None]
    return {"n": len(clean), "mean": statistics.mean(clean) if clean else "NOT RUN", "std": statistics.stdev(clean) if len(clean) > 1 else (0.0 if clean else "NOT RUN")}


def paired_stats(left, right, seed=SEED):
    pairs = [(a, b) for a, b in zip(left, right) if safe_number(a) is not None and safe_number(b) is not None]
    if len(pairs) < 2: return {"n": len(pairs), "p_value": "NOT RUN", "effect_size": "NOT RUN", "bootstrap_ci_95": "NOT RUN"}
    diffs = [a - b for a, b in pairs]; test = wilcoxon(diffs, method="auto")
    positive = sum(d > 0 for d in diffs); negative = sum(d < 0 for d in diffs)
    rng = random.Random(seed); boot = []
    for _ in range(2000): boot.append(statistics.mean(rng.choices(diffs, k=len(diffs))))
    boot.sort(); lo = boot[int(0.025 * len(boot))]; hi = boot[int(0.975 * len(boot))]
    return {"n": len(pairs), "p_value": float(test.pvalue), "effect_size_rank_biserial": (positive - negative) / (positive + negative) if positive + negative else 0.0, "bootstrap_ci_95": [lo, hi], "mean_difference": statistics.mean(diffs)}


def assert_finite_result(value, label):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"status", "reason", "error"} or isinstance(item, str): continue
            assert_finite_result(item, f"{label}.{key}")
    elif isinstance(value, list):
        for item in value: assert_finite_result(item, label)
    elif isinstance(value, float): assert math.isfinite(value), label


def load_app_pipeline():
    import sys
    backend = str(ROOT.parent / "backend")
    if backend not in sys.path: sys.path.insert(0, backend)
    from services.pipeline_service import build_prompt_package, keyword_intent_parser, multilingual_bert_parser
    return build_prompt_package, keyword_intent_parser, multilingual_bert_parser
