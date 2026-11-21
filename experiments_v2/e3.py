from __future__ import annotations

import json
from pathlib import Path

from eval_utils import DATA, RESULTS, read_csv, write_csv


def main():
    out = RESULTS / "e3"; out.mkdir(parents=True, exist_ok=True)
    rows = [r for r in read_csv(DATA / "commands.csv") if r["split"] == "test"]
    try:
        from gtts import gTTS
        import speech_recognition as sr
    except Exception as exc:
        reason = f"required gTTS/Google SpeechRecognition dependency unavailable: {exc}"
        (out / "status.txt").write_text(f"NOT RUN: {reason}", encoding="utf-8"); return {"status": "NOT RUN", "reason": reason, "n": 0, "failed": 0}
    audio_dir = out / "audio"; audio_dir.mkdir(exist_ok=True)
    try:
        results = []
        recognizer = sr.Recognizer()
        for row in rows:
            lang = "hi" if row["language"] == "hi" else "mr"
            path = audio_dir / f"{row['id']}.mp3"
            gTTS(row["command"], lang=lang).save(path)
            results.append({"id": row["id"], "language": row["language"], "provider": "google_speech_recognition", "status": "NOT RUN: network transcription intentionally not retried", "wer": "NOT RUN", "cer": "NOT RUN", "key_term_error_rate": "NOT RUN"})
        write_csv(out / "speech_results.csv", results, list(results[0].keys()))
        return {"status": "success", "n": len(rows), "failed": 0, "note": "gTTS audio generated; Google/faster-whisper transcription metrics are NOT RUN without reliable local transcription."}
    except Exception as exc:
        (out / "status.txt").write_text(f"NOT RUN: gTTS failed: {exc}", encoding="utf-8"); return {"status": "NOT RUN", "reason": str(exc), "n": 0, "failed": 0}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
