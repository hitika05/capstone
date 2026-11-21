#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results' / 'e4'


def main() -> int:
    scoring = RESULTS / 'scoring.csv'
    if not scoring.exists():
        print(f'Missing {scoring}. Run e4_devanagari.py first.')
        return 0

    rows = list(csv.DictReader(open(scoring, 'r', encoding='utf-8', newline='')))
    if not rows:
        print('No scoring rows found.')
        return 0

    out = RESULTS / 'aggregate.txt'
    out.write_text('Method-level summary\n\n' + '\n'.join(f"{r['method']}: {r['all_characters_correct']}" for r in rows), encoding='utf-8')
    print(f'Wrote aggregate summary to {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
