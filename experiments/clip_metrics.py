from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.stats import wilcoxon

MODEL_ID = "openai/clip-vit-base-patch32"


def score_rows(rows: list[dict], results_dir: Path) -> tuple[list[dict], str]:
    try:
        from transformers import CLIPModel, CLIPProcessor
        import torch
    except Exception as exc:
        return rows, f"NOT RUN: CLIP dependencies unavailable: {exc}"
    try:
        processor = CLIPProcessor.from_pretrained(MODEL_ID)
        model = CLIPModel.from_pretrained(MODEL_ID)
        model.eval()
        for row in rows:
            if row.get("status") != "success":
                row["clip_score"] = "NOT RUN: image failed"
                continue
            image = Image.open(row["image_path"]).convert("RGB")
            inputs = processor(text=[row["english_reference"]], images=image, return_tensors="pt", padding=True)
            with torch.no_grad():
                output = model(**inputs)
                image_features = output.image_embeds / output.image_embeds.norm(dim=-1, keepdim=True)
                text_features = output.text_embeds / output.text_embeds.norm(dim=-1, keepdim=True)
                row["clip_score"] = float((image_features @ text_features.T).item())
        return rows, ""
    except Exception as exc:
        return rows, f"NOT RUN: CLIP scoring failed: {exc}"


def write_stats(rows: list[dict], results_dir: Path) -> dict:
    stats = {}
    for condition in ("C1", "C2", "C3"):
        values = [float(row["clip_score"]) for row in rows if row["condition"] == condition and _number(row.get("clip_score"))]
        stats[condition] = {"n": len(values), "mean": float(np.mean(values)) if values else "NOT RUN", "std": float(np.std(values, ddof=1)) if len(values) > 1 else (0.0 if values else "NOT RUN")}
    paired = {}
    by_id = {(row["id"], row["condition"]): row for row in rows}
    for left, right in (("C3", "C1"), ("C3", "C2")):
        pairs = [(float(by_id[(key, left)]["clip_score"]), float(by_id[(key, right)]["clip_score"])) for key in {row["id"] for row in rows} if (key, left) in by_id and (key, right) in by_id and _number(by_id[(key, left)].get("clip_score")) and _number(by_id[(key, right)].get("clip_score"))]
        if len(pairs) < 2:
            paired[f"{left}_vs_{right}"] = {"n": len(pairs), "p_value": "NOT RUN", "effect_size": "NOT RUN"}
            continue
        differences = np.array([a - b for a, b in pairs], dtype=float)
        test = wilcoxon(differences, zero_method="wilcox", alternative="two-sided", method="auto")
        positive = int(np.sum(differences > 0)); negative = int(np.sum(differences < 0))
        effect = (positive - negative) / (positive + negative) if positive + negative else 0.0
        paired[f"{left}_vs_{right}"] = {"n": len(pairs), "p_value": float(test.pvalue), "effect_size_rank_biserial": float(effect)}
    stats["paired_tests"] = paired
    (results_dir / "clip_stats.json").write_text(__import__("json").dumps(stats, indent=2), encoding="utf-8")
    return stats


def make_example_grid(rows: list[dict], output_path: Path) -> None:
    from PIL import ImageDraw
    selected = [row for row in rows if row.get("status") == "success"][:9]
    if not selected:
        return
    thumb_w, thumb_h = 240, 300
    grid = Image.new("RGB", (thumb_w * 3, thumb_h * math.ceil(len(selected) / 3)), "white")
    draw = ImageDraw.Draw(grid)
    for index, row in enumerate(selected):
        image = Image.open(row["image_path"]).convert("RGB")
        image.thumbnail((thumb_w, thumb_h - 30))
        x = (index % 3) * thumb_w
        y = (index // 3) * thumb_h
        grid.paste(image, (x, y))
        draw.text((x + 4, y + thumb_h - 24), f"{row['id']} {row['condition']}", fill="black")
    grid.save(output_path)


def _number(value) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
