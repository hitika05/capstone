#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results'


def collect() -> dict:
    summary = {}
    for path in sorted(RESULTS.glob('*')):
        if path.is_dir():
            rel = path.name
            summary[rel] = {'status': 'run', 'files': sorted(str(p.relative_to(ROOT)) for p in path.rglob('*') if p.is_file())}
    return summary


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    summary = collect()
    md = RESULTS / 'summary.md'
    md.write_text('# Experiment summary\n\n' + '\n'.join(f'- **{k}**: {len(v["files"])} file(s) generated' for k, v in summary.items()), encoding='utf-8')
    with open(RESULTS / 'run_metadata.json', 'w', encoding='utf-8') as f:
        json.dump({
            'date': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'python': __import__('platform').python_version(),
            'os': __import__('platform').platform(),
            'experiments_run': sorted(summary.keys()),
            'notes': 'Smoke tests only; no paper results were computed without a full dataset or recorded audio.'
        }, f, indent=2)
    print(f'Wrote summary to {md} and metadata to {RESULTS / "run_metadata.json"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
