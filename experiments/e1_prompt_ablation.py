#!/usr/bin/env python3
"""Smoke-level prompt ablation for the evaluation section.

This script evaluates the same command under three conditions using runtime code from the app:
- C1 raw command
- C2 machine-translated English command
- C3 full prompt pipeline (intent parser + prompt builder + image generation)
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from deep_translator import GoogleTranslator
from PIL import Image, ImageDraw

from services.pipeline_service import build_prompt_package, parse_intent
from clip_metrics import make_example_grid, score_rows, write_stats
from image_backend import generate_image, stability_available

RESULTS_DIR = ROOT / "results" / "e1"
IMG_DIR = RESULTS_DIR / "images"
CSV_PATH = RESULTS_DIR / "clip_scores.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prompt ablation smoke test")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--backend", choices=["stability", "pollinations"], required=True)
    return parser.parse_args()


def translate_to_english(text: str) -> str:
    try:
        return GoogleTranslator(source="auto", target="en").translate(text) or text
    except Exception:
        return text


def run_condition(condition: str, prompt: str, reference: str, out_path: Path, backend: str):
    result = generate_image(prompt, out_path, backend)
    return {
        "condition": condition,
        "prompt_sent": prompt,
        "english_reference": reference,
        "image_path": result.path,
        "latency": round(result.latency, 3),
        "backend": result.backend,
        "model_name": result.model_name,
        "status": result.status,
    }


def run_condition_c3(command: str, reference: str, out_path: Path, backend: str):
    intent = parse_intent(command, mode="review")
    extracted = {
        "businessName": "Shop",
        "tagline": "Quality & Excellence",
        "services": ["Service", "Support"],
        "contact": "",
        "cta": "Order Now",
        "layoutType": "elegant",
        "brandColor": "#6366f1",
        "accentColor": "#fbbf24",
        "textContrast": "light",
    }
    pkg = build_prompt_package(intent, extracted, brand_profile={}, source_text=command)
    return run_condition("C3", pkg["prompt"], reference, out_path, backend)


def main() -> int:
    args = parse_args()
    if args.backend == "stability" and not stability_available():
        raise SystemExit("STABILITY_API_KEY is unavailable; Stability test was NOT RUN.")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    commands_file = ROOT / "data" / "commands.csv"
    if not commands_file.exists():
        print(f"Missing {commands_file}. Run prepare_data.py first.")
        return 1

    with open(commands_file, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))[: args.limit]

    clip_rows = []
    for row in rows:
        base_id = row["id"]
        command = row["command"]
        reference = row["english_reference"]
        english = translate_to_english(command)
        conditions = [("C1", command), ("C2", english)]
        intent = parse_intent(command, mode="review")
        extracted = {"businessName": "Shop", "tagline": "Quality & Excellence", "services": ["Service", "Support"], "contact": "", "cta": "Order Now", "layoutType": "elegant", "brandColor": "#6366f1", "accentColor": "#fbbf24", "textContrast": "light"}
        package = build_prompt_package(intent, extracted, brand_profile={}, source_text=command)
        conditions.append(("C3", package["prompt"]))
        for cond_name, prompt in conditions:
            out_path = IMG_DIR / f"{base_id}_{cond_name}.png"
            record = run_condition(cond_name, prompt, reference, out_path, args.backend)
            clip_rows.append({"id": base_id, **record, "clip_score": "NOT RUN"})

    backends = {row["backend"] for row in clip_rows if row["status"] == "success"}
    if len(backends) > 1:
        raise RuntimeError(f"Mixed image backends in E1: {sorted(backends)}")
    clip_rows, clip_note = score_rows(clip_rows, RESULTS_DIR)

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "condition", "prompt_sent", "english_reference", "backend", "model_name", "status", "latency", "clip_score", "image_path"])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in clip_rows)

    write_stats(clip_rows, RESULTS_DIR)
    make_example_grid(clip_rows, RESULTS_DIR / "example_grid.png")
    (RESULTS_DIR / "clip_note.txt").write_text(clip_note or "CLIP scores computed.", encoding="utf-8")

    print(f"Saved {len(clip_rows)} prompt-variant records to {CSV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
