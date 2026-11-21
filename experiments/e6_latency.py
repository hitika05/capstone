#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import numpy as np
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
BACKEND_ROOT = PROJECT_ROOT / 'backend'
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.pipeline_service import build_prompt_package, parse_intent
from image_backend import generate_image, stability_available

RESULTS_DIR = ROOT / 'results' / 'e6'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--backend', choices=['stability', 'pollinations'], required=True)
    args = parser.parse_args()
    if args.backend == 'stability' and not stability_available():
        raise SystemExit('STABILITY_API_KEY is unavailable; Stability test was NOT RUN.')
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    commands = ROOT / 'data' / 'commands.csv'
    if not commands.exists():
        print(f'Missing {commands}. Run prepare_data.py first.')
        return 1

    rows = list(csv.DictReader(open(commands, 'r', encoding='utf-8', newline='')))[: args.limit]
    timings = []
    for row in rows:
        start = time.perf_counter()
        intent = parse_intent(row['command'], mode='review')
        parse_t = time.perf_counter() - start
        extracted = {'businessName': 'Demo', 'tagline': 'Quality', 'services': ['One'], 'contact': '', 'cta': 'Call Now', 'layoutType': 'elegant', 'brandColor': '#6366f1', 'accentColor': '#fbbf24', 'textContrast': 'light'}
        pkg = build_prompt_package(intent, extracted, {}, source_text=row['command'])
        build_t = time.perf_counter() - start - parse_t
        gen_start = time.perf_counter()
        result = generate_image(pkg['prompt'], RESULTS_DIR / 'images' / f"{row['id']}.png", args.backend, negative_prompt=pkg['negative_prompt'])
        gen_t = time.perf_counter() - gen_start
        overlay_start = time.perf_counter()
        overlay_t = time.perf_counter() - overlay_start
        timings.append({'id': row['id'], 'parse_seconds': round(parse_t, 3), 'prompt_build_seconds': round(build_t, 3), 'image_seconds': round(gen_t, 3), 'overlay_seconds': round(overlay_t, 3), 'total_seconds': round(parse_t + build_t + gen_t + overlay_t, 3), 'backend': result.backend, 'model_name': result.model_name, 'status': result.status, 'image_path': result.path, 'error': result.error})

    out = RESULTS_DIR / 'latency.csv'
    with open(out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'parse_seconds', 'prompt_build_seconds', 'image_seconds', 'overlay_seconds', 'total_seconds', 'backend', 'model_name', 'status', 'image_path', 'error'])
        writer.writeheader(); writer.writerows(timings)

    stage_stats = {}
    for field in ('parse_seconds', 'prompt_build_seconds', 'image_seconds', 'overlay_seconds', 'total_seconds'):
        values = [float(row[field]) for row in timings]
        stage_stats[field] = {
            'n': len(values),
            'median': float(np.median(values)) if values else 'NOT RUN',
            'min': float(min(values)) if values else 'NOT RUN',
            'max': float(max(values)) if values else 'NOT RUN',
            'p95': float(np.percentile(values, 95)) if values else 'NOT RUN',
        }
    failures = sum(row['status'] != 'success' for row in timings)
    (RESULTS_DIR / 'latency_stats.json').write_text(json.dumps({'stages': stage_stats, 'backend_usage': {args.backend: len(timings)}, 'failure_count': failures, 'failure_rate': failures / len(timings) if timings else 'NOT RUN'}, indent=2), encoding='utf-8')

    print(f'Wrote latency smoke results to {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
