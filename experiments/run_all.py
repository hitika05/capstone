#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EXPERIMENTS = {
    'e1': ROOT / 'e1_prompt_ablation.py',
    'e2': ROOT / 'e2_intent_accuracy.py',
    'e3': ROOT / 'e3_asr_wer.py',
    'e4': ROOT / 'e4_devanagari.py',
    'e5': ROOT / 'e5_price_list.py',
    'e6': ROOT / 'e6_latency.py',
}


def main() -> int:
    parser = argparse.ArgumentParser(description='Run experimental smoke tests or full evaluations.')
    parser.add_argument('--only', default='e1,e2,e3,e4,e5,e6')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--backend', choices=['stability', 'pollinations'], default='pollinations')
    args = parser.parse_args()

    selected = [item.strip() for item in args.only.split(',') if item.strip()]
    for key in selected:
        if key not in EXPERIMENTS:
            print(f'Unknown experiment: {key}')
            continue
        script = EXPERIMENTS[key]
        cmd = [sys.executable, str(script)]
        if args.limit is not None:
            cmd.extend(['--limit', str(args.limit)])
        if key in {'e1', 'e4', 'e6'}:
            cmd.extend(['--backend', args.backend])
        print('\nRunning:', ' '.join(cmd))
        subprocess.run(cmd, check=False, cwd=str(ROOT))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
