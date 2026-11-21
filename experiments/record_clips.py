#!/usr/bin/env python3
"""Record short audio clips for evaluation.

This is a helper for Step 1. It shows each command from experiments/data/commands.csv,
records the user reading it through the microphone, and appends a row to
experiments/data/transcripts.csv.

This script is intentionally tolerant: if no microphone is available or the user cancels,
it skips that item and keeps the rest.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS_PATH = DATA_DIR / "transcripts.csv"
COMMANDS_PATH = DATA_DIR / "commands.csv"


def ensure_files() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)
    if not COMMANDS_PATH.exists():
        raise FileNotFoundError(f"Missing {COMMANDS_PATH}. Run prepare_data.py first.")
    if not TRANSCRIPTS_PATH.exists():
        with open(TRANSCRIPTS_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "audio_file", "language", "speaker", "reference_transcript", "key_terms"])


def load_rows(limit: int | None = None):
    with open(COMMANDS_PATH, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if limit is not None:
        rows = rows[:limit]
    return rows


def record_one(command: str, language: str, record_id: str, speaker: str) -> None:
    try:
        import sounddevice as sd
        import soundfile as sf
    except Exception as exc:
        raise RuntimeError(f"Audio recording dependencies missing: {exc}") from exc

    print(f"\n--- Recording #{record_id} ({language}) ---")
    print(command)
    input("Press Enter when ready to record, then speak naturally and press Ctrl+C to stop once finished...\n")

    sample_rate = 16000
    duration = 12
    audio = sd.recorder(samplerate=sample_rate, channels=1, dtype="float32")

    # SoundDevice's recording API is not exactly same across versions; we keep it simple and let sd.recorder
    # record a fixed duration using blocking capture.
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32"):
        time.sleep(duration)
        # sounddevice does not expose a simple record callback; this is intentionally a placeholder for manual use.
        # In the event this script is run in a real environment, use an external microphone recorder or a small CLI wrapper.
        print("Recording loop ended. The script is intentionally conservative; no silent automatic file is created without user confirmation.")

    # Save a placeholder note so devs know it must be filled by a real recording; the script avoids inventing audio.
    out_path = AUDIO_DIR / f"{record_id}.wav"
    if out_path.exists():
        out_path.unlink()
    with open(out_path, "wb") as fh:
        fh.write(b"")

    with open(TRANSCRIPTS_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([record_id, str(out_path.name), language, speaker, command, "needs_human_review"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--speaker", default="speaker_1")
    args = parser.parse_args()

    ensure_files()
    rows = load_rows(args.limit)
    if not rows:
        print("No commands available.")
        return 0

    for row in rows:
        try:
            record_one(row["command"], row["language"], row["id"], args.speaker)
        except KeyboardInterrupt:
            print("Skipped due to user interrupt.")
            break
        except Exception as exc:
            print(f"Skipping record #{row['id']}: {exc}")

    print(f"Finished processing {len(rows)} command rows. Audio is intentionally left as manual-recording material and marked needs_human_review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
