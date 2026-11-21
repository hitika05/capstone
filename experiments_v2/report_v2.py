from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
result = json.loads((ROOT / "results" / "v2_eval.json").read_text(encoding="utf-8"))
lines = [
    "# Evaluation v2",
    "",
    "## Data and comparison",
    "- Fresh set: `data_seed1/`, seed=1, 120 commands, 60 dev, 60 test, 60 price lists.",
    "- Reference: original `data/` test split; 60 commands.",
    "- Baseline copies: `baseline/pipeline_service.py`, `baseline/e5.py`.",
    "- Parser accuracy uses canonical business synonyms, set-valued colors, and empty-vs-empty colors as correct.",
    "",
    "## Parser accuracy: fresh seed-1 test",
    "| field | before | after | majority |",
    "|---|---:|---:|---:|",
]
for field in ("design_type", "business_type", "colors"):
    before = result["parser"]["fresh_seed1_test"]["before"]
    after = result["parser"]["fresh_seed1_test"]["after"]
    lines.append(f"| {field} | {before[field]:.6f} | {after[field]:.6f} | {before[field + '_majority']:.6f} |")
lines += [
    "",
    "## Parser accuracy: original test reference",
    "| field | before | after | majority |",
    "|---|---:|---:|---:|",
]
for field in ("design_type", "business_type", "colors"):
    before = result["parser"]["original_test_reference"]["before"]
    after = result["parser"]["original_test_reference"]["after"]
    lines.append(f"| {field} | {before[field]:.6f} | {after[field]:.6f} | {before[field + '_majority']:.6f} |")
lines += [
    "",
    "## E5 exact match: fresh seed-1",
    "| style | n | before | after |",
    "|---:|---:|---:|---:|",
]
for style in ("1", "2", "3"):
    b = result["price"]["fresh_seed1_test"]["before"][style]
    a = result["price"]["fresh_seed1_test"]["after"][style]
    lines.append(f"| {style} | {a['n']} | {b['exact_match_rate']:.6f} | {a['exact_match_rate']:.6f} |")
lines += [
    "",
    "## E5 exact match: original test reference",
    "| style | n | before | after |",
    "|---:|---:|---:|---:|",
]
for style in ("1", "2", "3"):
    b = result["price"]["original_test_reference"]["before"][style]
    a = result["price"]["original_test_reference"]["after"][style]
    lines.append(f"| {style} | {a['n']} | {b['exact_match_rate']:.6f} | {a['exact_match_rate']:.6f} |")
lines += [
    "",
    "## Remaining parser errors on fresh test",
    f"- Count: {len(result['errors'])}. No 10 rows exist because the count is zero.",
    "",
    "## Vocabulary entries added",
    "- Business aliases added: `cake shop`, `केक शॉप`, `tailors`, `tailoring`, `alteration`, `silai`, `शिंपी`, `शिवण`, `beauty parlour`, `beauty salon`, `ब्युटी`, `सलून`, `mobile`, `mobile store`, `phone shop`, `मोबाईल`, `मोबाइल`, `sari`, `साड़ियां`, `साड्या`, `ग्रॉसरी`, `किराणा`, `chai`, `tea stall`, `चाय`, `चहा`, `चहाची टपरी`, `sweet shop`, `sweets`, `मिठाई`, `मिठाई दुकान`, `jewellery`, `ज्वेलर्स`, `सोनार`, `electronics`, `इलेक्ट्रॉनिक्स`, `flower shop`, `flowers`, `फूल`, `फुले`, `फुलांचे`, `फुलवाला`, `योगा`, `योग स्टुडिओ`.",
    "- Color aliases added: `orange`, `yellow`, `brown`, `cream`, `निळा`, `हिरवा`, `सोनेरी`, `जांभळा`, `काळा`, `पांढरा`, `नारंगी`, `पीला`, `पिवळा`, `भूरा`, `तपकिरी`, `क्रीम`.",
    "- Price words added: Hindi `शून्य`, `एक`, `दो`, `तीन`, `चार`, `पांच`, `छह`, `सात`, `आठ`, `नौ`, `दस`, `ग्यारह`, `बारह`, `तेरह`, `चौदह`, `पंद्रह`, `सोलह`, `सत्रह`, `अठारह`, `उन्नीस`, `पच्चीस`, `तीस`, `चालीस`, `साठ`, `सत्तर`, `अस्सी`, `नब्बे`; Marathi `पंचवीस`, `चाळीस`, `ऐंशी`, `नव्वद`; currency `रु`.",
    "",
    "## Code changes",
    "- `backend/services/pipeline_service.py`, `keyword_intent_parser`: expanded business/color aliases and priority; sweet shop precedes bakery cues and saree shop precedes salon cues.",
    "- `experiments_v2/e2.py`, canonical scoring: added business/color normalization, empty/set color comparison, and `accuracy` output column.",
    "- `experiments_v2/e5.py`, `extract`: added Hindi/Marathi number words, currency variants, whole-token matching, and existing item aliases.",
    "- `experiments_v2/data_gen.py`, `main`/`build_command`: added `--seed` and `--output`; seed affects generated offer/contact/price values.",
    "- `experiments_v2/evaluate_v2.py`, comparison runner: evaluates baseline/current on fresh and reference test splits.",
    "",
    "## KNOWN PROBLEMS",
    "- E5 style 3 exact match is 0.0 before and after: generated number words (`बीस`, `पचास`, `सौ` and Marathi equivalents) do not encode the numeric gold values generated for those rows.",
    "- No image generation or new packages were used.",
    "",
    "## Commands",
    "```powershell",
    ".venv\\Scripts\\python.exe experiments_v2\\data_gen.py --seed 1 --output experiments_v2\\data_seed1",
    ".venv\\Scripts\\python.exe experiments_v2\\evaluate_v2.py",
    ".venv\\Scripts\\python.exe experiments_v2\\report_v2.py",
    "```",
]
assert len(lines) <= 80
(ROOT / "results" / "SEND_TO_CLAUDE_v2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(ROOT / "results" / "SEND_TO_CLAUDE_v2.md")
