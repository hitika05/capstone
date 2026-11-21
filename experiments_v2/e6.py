from __future__ import annotations

import json
import statistics
import time

from eval_utils import DATA, RESULTS, read_csv
from gen import environment, generate


def percentile(values, p):
    values = sorted(values); return values[min(len(values) - 1, int(len(values) * p))] if values else "NOT RUN"


def main():
    out = RESULTS / "e6"; out.mkdir(parents=True, exist_ok=True)
    rows = read_csv(DATA / "commands.csv")[:30]; timings = []
    try:
        from eval_utils import load_app_pipeline
        build_prompt_package, keyword_parser, _ = load_app_pipeline()
        for row in rows:
            start = time.perf_counter(); intent = keyword_parser(row["command"]); parse_seconds = time.perf_counter() - start
            extracted = {"businessName": row["shop_name"], "services": json.loads(row["services"]), "contact": row["contact"], "brandColor": ""}
            start = time.perf_counter(); package = build_prompt_package(intent, extracted, {}, source_text=row["command"]); prompt_seconds = time.perf_counter() - start
            image = generate(package["prompt"], 1000 + int(row["id"]), out / "images" / f"{row['id']}.png")
            timings.append({"id": row["id"], "parse_seconds": parse_seconds, "prompt_build_seconds": prompt_seconds, "image_seconds": image["latency"], "overlay_seconds": "NOT RUN: frontend overlay", "total_seconds": parse_seconds + prompt_seconds + image["latency"], "status": image["status"], "error": image.get("error", "")})
        with open(out / "latency.json", "w", encoding="utf-8") as handle: json.dump(timings, handle, indent=2)
        stats = {field: {"n": len(timings), "median": statistics.median([r[field] for r in timings]), "min": min(r[field] for r in timings), "max": max(r[field] for r in timings), "p95": percentile([r[field] for r in timings], .95)} for field in ("parse_seconds", "prompt_build_seconds", "image_seconds", "total_seconds")}
        stats["overlay_seconds"] = "NOT RUN: overlay is frontend-owned"
        stats["environment"] = environment(); stats["failed"] = sum(r["status"] == "failed" for r in timings); stats["failure_rate"] = stats["failed"] / len(timings)
        (out / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        return {"status": "success", "n": len(timings), "failed": stats["failed"], "stats": stats}
    except Exception as exc:
        (out / "error.txt").write_text(f"NOT RUN: {exc}", encoding="utf-8"); return {"status": "NOT RUN", "reason": str(exc), "n": 0, "failed": 0}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
