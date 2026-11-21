from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import quote
import os
import requests


@dataclass
class ImageResult:
    backend: str
    model_name: str
    status: str
    path: str
    latency: float
    error: str = ""


MODELS = {
    "stability": "stable-image-core",
    "pollinations": "flux",
}


def stability_available() -> bool:
    key = os.getenv("STABILITY_API_KEY", "").strip()
    return bool(key and key != "your_key_here")


def generate_image(prompt: str, output_path: Path, backend: str, negative_prompt: str = "", retries: int = 5) -> ImageResult:
    if backend not in MODELS:
        raise ValueError(f"Unsupported image backend: {backend}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    last_error = ""
    started = time.perf_counter()
    for attempt in range(retries):
        try:
            if backend == "stability":
                response = _stability_request(prompt, negative_prompt)
            else:
                response = _pollinations_request(prompt)
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}: {response.text[:500]}"
                raise RuntimeError(last_error)
            content_type = response.headers.get("content-type", "")
            if "image" not in content_type.lower():
                last_error = f"unexpected content type: {content_type}"
                raise RuntimeError(last_error)
            output_path.write_bytes(response.content)
            return ImageResult(backend, MODELS[backend], "success", str(output_path), time.perf_counter() - started)
        except Exception as exc:
            last_error = str(exc)
            if attempt < retries - 1:
                time.sleep(0.25 * (2 ** attempt))
    return ImageResult(backend, MODELS[backend], "failed", "", time.perf_counter() - started, last_error)


def _stability_request(prompt: str, negative_prompt: str) -> requests.Response:
    key = os.getenv("STABILITY_API_KEY", "").strip()
    if not key or key == "your_key_here":
        raise RuntimeError("STABILITY_API_KEY is unavailable")
    return requests.post(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        headers={"Authorization": f"Bearer {key}", "Accept": "image/*"},
        files={"none": ""},
        data={
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "aspect_ratio": "4:5",
            "output_format": "png",
        },
        timeout=15,
    )


def _pollinations_request(prompt: str) -> requests.Response:
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1080&height=1350&nologo=true&model={MODELS['pollinations']}"
    return requests.get(url, timeout=15)
