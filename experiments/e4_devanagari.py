#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
BACKEND_ROOT = PROJECT_ROOT / 'backend'
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from PIL import Image, ImageDraw, ImageFont
from image_backend import generate_image, stability_available

RESULTS_DIR = ROOT / 'results' / 'e4'
IMG_DIR = RESULTS_DIR / 'images'


def make_sheet(command: str, idx: int) -> str:
    img = Image.new('RGB', (1400, 900), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), 'Method A: Devanagari prompt text', fill=(0,0,0), font=ImageFont.load_default())
    draw.text((50, 100), command[:80], fill=(20,20,20), font=ImageFont.load_default())
    draw.text((50, 180), 'Method B: pipeline overlay', fill=(0,0,0), font=ImageFont.load_default())
    out = IMG_DIR / f'command_{idx}_sheet.png'
    img.save(out)
    return str(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--backend', choices=['stability', 'pollinations'], required=True)
    args = parser.parse_args()
    if args.backend == 'stability' and not stability_available():
        raise SystemExit('STABILITY_API_KEY is unavailable; Stability test was NOT RUN.')
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    commands = ROOT / 'data' / 'commands.csv'
    if not commands.exists():
        print(f'Missing {commands}. Run prepare_data.py first.')
        return 1

    rows = list(csv.DictReader(open(commands, 'r', encoding='utf-8', newline='')))[: args.limit]
    scoring = []
    for idx, row in enumerate(rows, start=1):
        prompt_path = make_sheet(row['command'], idx)
        try:
            direct = generate_image(row['command'], RESULTS_DIR / 'images' / f"{row['id']}_direct.png", args.backend)
            pipeline = generate_image(row['english_reference'], RESULTS_DIR / 'images' / f"{row['id']}_pipeline.png", args.backend)
            scoring.append({'id': row['id'], 'method': 'devanagari_prompt', 'backend': direct.backend, 'model_name': direct.model_name, 'status': direct.status, 'all_characters_correct': 'PENDING HUMAN SCORING', 'notes': direct.path or direct.error})
            scoring.append({'id': row['id'], 'method': 'pipeline_overlay', 'backend': pipeline.backend, 'model_name': pipeline.model_name, 'status': pipeline.status, 'all_characters_correct': 'PENDING HUMAN SCORING', 'notes': pipeline.path or pipeline.error})
        except Exception as exc:
            scoring.append({'id': row['id'], 'method': 'pipeline_overlay', 'all_characters_correct': 'needs_human_review', 'notes': str(exc)})

    out = RESULTS_DIR / 'scoring.csv'
    with open(out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'method', 'backend', 'model_name', 'status', 'all_characters_correct', 'notes'])
        writer.writeheader(); writer.writerows(scoring)

    print(f'Generated Devanagari smoke sheets and scoring file in {RESULTS_DIR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
