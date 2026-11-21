from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache"
IMAGES = ROOT / "results" / "images"
MODEL_NAME = "stabilityai/sdxl-turbo" if torch.cuda.is_available() else "stabilityai/sd-turbo"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = "fp16" if torch.cuda.is_available() else "fp32"

_PIPELINE = None


def environment():
    return {"model": MODEL_NAME, "device": DEVICE, "dtype": DTYPE, "cuda": torch.cuda.is_available(), "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"}


def load_pipeline():
    global _PIPELINE
    if _PIPELINE is not None:
        return _PIPELINE
    try:
        from diffusers import AutoPipelineForText2Image
        kwargs = {"torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32}
        _PIPELINE = AutoPipelineForText2Image.from_pretrained(MODEL_NAME, **kwargs).to(DEVICE)
        return _PIPELINE
    except Exception as exc:
        raise RuntimeError(f"local diffusers model unavailable: {exc}") from exc


def generate(prompt: str, seed: int, output_path: Path) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(json.dumps([prompt, seed, MODEL_NAME], sort_keys=True).encode()).hexdigest()
    cached = CACHE / f"{cache_key}.png"
    started = time.perf_counter()
    try:
        if cached.exists():
            output_path.write_bytes(cached.read_bytes())
            return {"status": "success", "path": str(output_path), "latency": time.perf_counter() - started, "cache": True, "model": MODEL_NAME}
        pipeline = load_pipeline()
        generator = torch.Generator(device=DEVICE).manual_seed(seed)
        image = pipeline(prompt=prompt, num_inference_steps=2, guidance_scale=0.0, height=512, width=512, generator=generator).images[0]
        image.save(cached); output_path.write_bytes(cached.read_bytes())
        return {"status": "success", "path": str(output_path), "latency": time.perf_counter() - started, "cache": False, "model": MODEL_NAME}
    except Exception as exc:
        return {"status": "failed", "path": "", "latency": time.perf_counter() - started, "cache": False, "model": MODEL_NAME, "error": str(exc)}


def timing_probe() -> dict:
    probe = []
    for index in range(2):
        probe.append(generate(f"offline timing probe {index}", 9000 + index, ROOT / "results" / "probe" / f"{index}.png"))
    return {"environment": environment(), "runs": probe, "total_seconds": sum(item["latency"] for item in probe)}
