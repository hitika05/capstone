from __future__ import annotations

import csv
import json
from pathlib import Path

from eval_utils import DATA, RESULTS, paired_stats, read_csv, summarize, write_csv
from gen import generate, timing_probe


def main():
    out = RESULTS / "e1"; out.mkdir(parents=True, exist_ok=True)
    rows = [r for r in read_csv(DATA / "commands.csv") if r["split"] == "test"]
    result_rows = []
    try:
        probe = timing_probe(); (out / "timing_probe.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
        if probe["total_seconds"] > 5400 and not probe["environment"]["cuda"]:
            selected = rows[:30]
        else:
            selected = rows
        (out / "selected_count.txt").write_text(str(len(selected)), encoding="utf-8")
        build_prompt_package, keyword_parser, _ = __import__("eval_utils").load_app_pipeline()
        for row in selected:
            extracted = {"businessName": row["shop_name"], "tagline": "", "services": json.loads(row["services"]), "contact": row["contact"], "cta": "Call Now", "brandColor": "", "accentColor": "", "textContrast": "light"}
            intent = keyword_parser(row["command"])
            package = build_prompt_package(intent, extracted, {}, source_text=row["command"])
            prompts = {"C1": row["command"], "C2": row["english_reference"], "C3": package["prompt"]}
            for condition, prompt in prompts.items():
                image = generate(prompt, 1000 + int(row["id"]), out / "images" / f"{row['id']}_{condition}.png")
                result_rows.append({"id": row["id"], "language": row["language"], "condition": condition, "prompt_sent": prompt, "english_reference": row["english_reference"], "status": image["status"], "latency": image["latency"], "image_path": image.get("path", ""), "clip_score": "NOT RUN", "business_clip_accuracy": "NOT RUN", "color_match": "NOT RUN", "error": image.get("error", "")})
        write_csv(out / "clip_scores.csv", result_rows, list(result_rows[0].keys()) if result_rows else ["id", "condition", "status"])
        successful = [r for r in result_rows if r["status"] == "success"]
        if successful:
            try:
                from transformers import CLIPModel, CLIPProcessor
                from PIL import Image
                import torch
                model_id = "openai/clip-vit-base-patch32"; processor = CLIPProcessor.from_pretrained(model_id); model = CLIPModel.from_pretrained(model_id).eval()
                taxonomy = json.loads((DATA / "taxonomy.json").read_text(encoding="utf-8"))
                for item in successful:
                    image = Image.open(item["image_path"]).convert("RGB")
                    inputs = processor(text=[item["english_reference"]], images=image, return_tensors="pt", padding=True)
                    with torch.no_grad():
                        output = model(**inputs); item["clip_score"] = float(torch.nn.functional.cosine_similarity(output.image_embeds, output.text_embeds).item())
                    if item["condition"] == "C3":
                        options = taxonomy["business_type"]; texts = [f"a photo of a {x}" for x in options]; inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)
                        with torch.no_grad():
                            predicted_index = int(model(**inputs).logits_per_image[0].argmax())
                        gold_type = next(r for r in rows if r["id"] == item["id"])["business_type"]
                        item["business_clip_accuracy"] = predicted_index == options.index(gold_type)
                (out / "clip_model.txt").write_text(model_id, encoding="utf-8")
            except Exception as exc:
                (out / "clip_note.txt").write_text(f"NOT RUN: CLIP scoring unavailable: {exc}", encoding="utf-8")
        write_csv(out / "clip_scores.csv", result_rows, list(result_rows[0].keys()) if result_rows else ["id", "condition", "status"])
        stats = {c: summarize([r["clip_score"] for r in result_rows if r["condition"] == c and r["status"] == "success"]) for c in ("C1", "C2", "C3")}
        by_id = {r["id"]: {} for r in result_rows}
        for r in result_rows: by_id[r["id"]][r["condition"]] = r["clip_score"]
        c1 = [v.get("C1") for v in by_id.values()]; c2 = [v.get("C2") for v in by_id.values()]; c3 = [v.get("C3") for v in by_id.values()]
        stats["C3_vs_C1"] = paired_stats(c3, c1); stats["C3_vs_C2"] = paired_stats(c3, c2)
        (out / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        return {"status": "success", "n": len(selected), "failed": sum(r["status"] == "failed" for r in result_rows), "stats": stats}
    except Exception as exc:
        (out / "error.txt").write_text(f"NOT RUN: {exc}", encoding="utf-8")
        return {"status": "NOT RUN", "reason": str(exc), "n": 0, "failed": 0}


if __name__ == "__main__": print(json.dumps(main(), indent=2))
