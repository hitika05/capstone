#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results' / 'e1'


def main() -> int:
    ratings_files = list((RESULTS).glob('rating_sheet*.csv'))
    if not ratings_files:
        print(f'No rating sheets found under {RESULTS}. Generate one with e1_prompt_ablation.py or fill it manually.')
        return 0

    rows = []
    for f in ratings_files:
        with open(f, 'r', encoding='utf-8', newline='') as handle:
            rows.extend(list(csv.DictReader(handle)))

    if not rows:
        print('No rows found in rating sheets.')
        return 0

    out = RESULTS / 'aggregate_ratings.csv'
    with open(out, 'w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['image_id', 'relevance_1to5', 'layout_1to5', 'quality_1to5'])
        writer.writeheader(); writer.writerows(rows)

    print(f'Aggregated rating rows into {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
