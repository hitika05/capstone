"""Presentation demo for the planned Indic-language model adaptation.

This is an evaluation/prototype demo, not a claim that the production model is
already fine-tuned. It compares a deliberately English-only baseline with the
current Indic-aware extraction path and writes a JSON report for review.
"""

import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from services.ai_service import extract_business_details  # noqa: E402


EXAMPLES = [
    {
        "label": "Hindi - tailoring",
        "prompt": "शिव टेलर्स के लिए इंस्टाग्राम पोस्ट बनाएं। सेवाएं: कपड़ों की सिलाई, अल्टरशन और ब्लाउज डिजाइन। नीले और सुनहरे रंग रखें। CTA: अभी ऑर्डर करें।",
    },
    {
        "label": "Marathi - homemade food",
        "prompt": "सह्याद्री कॅटरिंग साठी इंस्टाग्राम पोस्ट बनवा. सेवा: घरगुती जेवण, डबा सेवा आणि पार्टी कॅटरिंग. हिरवा आणि केशरी रंग वापरा. CTA: आजच ऑर्डर करा.",
    },
    {
        "label": "Hindi - aquarium service",
        "prompt": "ब्लू रीफ एक्वेरियम के लिए पोस्ट बनाएं। सेवाएं: एक्वेरियम सफाई, मछली की देखभाल और पानी की जांच। नीली रोशनी और रंगीन मछलियां दिखाएं। CTA: आज ही संपर्क करें।",
    },
]


def english_only_baseline(prompt: str) -> dict:
    """Small baseline representing an English-only extraction approach."""
    english_words = re.findall(r"[A-Za-z][A-Za-z -]{2,}", prompt)
    return {
        "businessName": english_words[0].strip() if english_words else "Unknown Business",
        "services": [],
        "cta": "",
        "visualTheme": "Generic promotional image",
    }


def compact(data: dict) -> dict:
    return {
        "businessName": data.get("businessName", ""),
        "services": data.get("services", []),
        "cta": data.get("cta", ""),
        "visualTheme": data.get("visualTheme", ""),
    }


def main() -> None:
    report = {
        "title": "VoiceDesign AI - Indic Language Adaptation Prototype",
        "status": "Prototype evaluation; fine-tuned model integration pending",
        "cases": [],
    }

    print("VoiceDesign AI | Indic Language Adaptation Prototype")
    print("Status: prototype evaluation; fine-tuned model integration pending\n")

    for example in EXAMPLES:
        baseline = english_only_baseline(example["prompt"])
        adapted = compact(extract_business_details(example["prompt"]))
        report["cases"].append({
            "label": example["label"],
            "prompt": example["prompt"],
            "baseline": baseline,
            "indic_adapted": adapted,
        })

        print(f"--- {example['label']} ---")
        print(f"Prompt: {example['prompt']}")
        print(f"Baseline: {json.dumps(baseline, ensure_ascii=False)}")
        print(f"Indic-aware: {json.dumps(adapted, ensure_ascii=False)}")
        print()

    output_path = ROOT / "scratch" / "indic_adaptation_demo_report.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
