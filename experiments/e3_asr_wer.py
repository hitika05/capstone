#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / 'results' / 'e3'
DATA_DIR = ROOT / 'data'
AUDIO_DIR = DATA_DIR / 'audio'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=3)
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not AUDIO_DIR.exists() or not any(AUDIO_DIR.iterdir()):
        print('ASR experiment skipped: no recorded audio in data/audio/. Run record_clips.py first and record at least one clip.')
        return 0

    transcripts = DATA_DIR / 'transcripts.csv'
    if not transcripts.exists():
        print('ASR experiment skipped: missing transcripts.csv. Run prepare_data.py or record_clips.py.')
        return 0

    rows = list(csv.DictReader(open(transcripts, 'r', encoding='utf-8', newline='')))[: args.limit]
    out = RESULTS_DIR / 'asr_results.csv'
    with open(out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'audio_file', 'language', 'status'])
        writer.writeheader()
        for row in rows:
            writer.writerow({'id': row['id'], 'audio_file': row['audio_file'], 'language': row['language'], 'status': 'skipped_no_live_asr_run_in_smoke_test'})

    print(f'ASR smoke placeholder wrote {len(rows)} rows to {out}; no real model transcription was run because the audio data was not recorded.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
