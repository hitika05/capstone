import asyncio
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import shutil
from deep_translator import GoogleTranslator

from services.ai_service import transcribe_audio, extract_business_details
from services.pipeline_service import (
    parse_intent,
    load_brand_memory,
    save_brand_memory,
    build_prompt_package,
    build_refinement_prompt,
    generate_routed_designs,
    log_variant_choice,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
GENERATIONS_DIR = os.path.join(BASE_DIR, "generations")

app = FastAPI(title="VoiceDesign AI")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(GENERATIONS_DIR, exist_ok=True)

# Mount static files
app.mount("/generations", StaticFiles(directory=GENERATIONS_DIR), name="generations")

@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...), spoken_lang: str = Form("en-US")):
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Speech recognition performs blocking audio conversion and network I/O.
        # Keep it off the event loop so the API remains responsive during STT.
        text = await asyncio.to_thread(transcribe_audio, file_path, spoken_lang)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DesignRequest(BaseModel):
    prompt: str
    overlay_lang: str = "English"
    user_id: Optional[str] = None
    final_submission: bool = False
    parsed_intent: Optional[Dict[str, Any]] = None


class IntentRequest(BaseModel):
    text: str
    mode: str = "review"
    user_id: Optional[str] = None


class VariantChoiceRequest(BaseModel):
    user_id: Optional[str] = None
    chosen_variant: str
    intent: Dict[str, Any]


class BrandMemorySaveRequest(BaseModel):
    user_id: str
    profile: Dict[str, Any]


class RefineDesignRequest(BaseModel):
    prompt: str
    refinement_command: str
    overlay_lang: str = "English"
    user_id: Optional[str] = None
    parsed_intent: Optional[Dict[str, Any]] = None


def _translate_text(text: str, target_lang: str) -> str:
    if not text:
        return text
    normalized = " ".join(str(text).strip().lower().split())
    percentage_match = re.fullmatch(r"(\d{1,3})%\s*off", normalized)
    if percentage_match:
        suffix = "छूट" if target_lang == "hi" else "सूट"
        return f"{percentage_match.group(1)}% {suffix}"
    local_translations = {
        "hi": {
            "stylish and colorful": "स्टाइलिश और रंगीन",
            "kids wear": "बच्चों के कपड़े",
            "latest designs": "नवीनतम डिज़ाइन",
            "seasonal offers": "मौसमी ऑफर",
            "shop now": "अभी खरीदें",
            "order now": "अभी ऑर्डर करें",
            "book now": "अभी बुक करें",
            "contact us": "हमसे संपर्क करें",
            "baked fresh daily": "हर दिन ताज़ा बेक किया हुआ",
            "custom cakes": "कस्टम केक",
            "designer pastries": "डिज़ाइनर पेस्ट्री",
            "wedding orders": "शादी के ऑर्डर",
            "quality assured": "गुणवत्ता की गारंटी",
            "premium quality": "प्रीमियम गुणवत्ता",
        },
        "mr": {
            "stylish and colorful": "स्टायलिश आणि रंगीबेरंगी",
            "kids wear": "मुलांचे कपडे",
            "latest designs": "नवीन डिझाईन्स",
            "seasonal offers": "हंगामी ऑफर",
            "shop now": "आता खरेदी करा",
            "order now": "आता ऑर्डर करा",
            "book now": "आता बुक करा",
            "contact us": "आमच्याशी संपर्क करा",
            "baked fresh daily": "दररोज ताजे बेक केलेले",
            "custom cakes": "कस्टम केक",
            "designer pastries": "डिझायनर पेस्ट्री",
            "wedding orders": "लग्नाच्या ऑर्डर्स",
            "quality assured": "गुणवत्तेची हमी",
            "premium quality": "प्रीमियम गुणवत्ता",
        },
    }
    fallback = local_translations.get(target_lang, {}).get(normalized)
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        if not translated:
            return fallback or text
        lowered = str(translated).lower()
        if "error 500" in lowered or "that\u00e2s an error" in lowered or "please try again later" in lowered:
            return fallback or text
        # The translator can return the original English text when its
        # service is unavailable. Prefer our deterministic UI vocabulary.
        if str(translated).strip().lower() == normalized and fallback:
            return fallback
        return translated
    except Exception:
        return fallback or text


def _translate_for_overlay(data: dict, overlay_lang: str) -> dict:
    if overlay_lang not in ["Hindi", "Marathi"]:
        return data

    target = 'hi' if overlay_lang == "Hindi" else 'mr'
    translated = dict(data)

    # Keep business names stable and user-authentic; avoid noisy translator artifacts.
    translated["businessName"] = str(data.get("businessName", ""))
    translated["tagline"] = _translate_text(str(data.get("tagline", "")), target)
    translated["cta"] = _translate_text(str(data.get("cta", "")), target)
    translated["services"] = [
        _translate_text(str(s), target) for s in data.get("services", [])
    ]

    # Keep contact numbers/emails intact; translate only label-like contact parts.
    contact = str(data.get("contact", ""))
    if contact and "@" not in contact:
        translated["contact"] = _translate_text(contact, target)
    else:
        translated["contact"] = contact

    return translated

@app.post("/generate-design")
async def create_design(request: DesignRequest):
    try:
        # Stage 3: Extract marketing details and intent.
        data = extract_business_details(request.prompt)
        intent = request.parsed_intent or parse_intent(
            request.prompt,
            mode="final" if request.final_submission else "review"
        )
        brand_profile = load_brand_memory(request.user_id)

        # Stage 4: Build prompt and negative prompt.
        prompt_package = build_prompt_package(intent, data, brand_profile, source_text=request.prompt)

        # Review only needs structured extraction. Defer image generation until
        # the user confirms the edited details so the review screen is instant.
        generated_paths = []
        if request.final_submission:
            generated_paths = generate_routed_designs(
                prompt_package=prompt_package,
                extracted_data=data,
                source_text=request.prompt,
                final_submission=True,
            )

        # Keep generated image raw; frontend applies themed text overlay.
        # Translate only user-facing text fields for overlay/response.
        ui_data = _translate_for_overlay(data, request.overlay_lang)

        business_name = ui_data.get("businessName", "")
        tagline = ui_data.get("tagline", "")
        contact = ui_data.get("contact", "")
        services = ui_data.get("services", [])
        
        # Return URL and structured data
        filename = os.path.basename(generated_paths[0]) if generated_paths else ""
        variants = []
        for i, p in enumerate(generated_paths):
            variants.append({
                "variant_id": "A" if i == 0 else f"V{i+1}",
                "image_url": f"http://127.0.0.1:8000/generations/{os.path.basename(p)}"
            })

        return {
            "image_url": f"http://127.0.0.1:8000/generations/{filename}" if filename else "",
            "variants": variants,
            "business_name": business_name,
            "tagline": tagline,
            "services": services,
            "contact": contact,
            "cta": ui_data.get("cta", ""),
            "layout_type": data.get("layoutType", "elegant"),
            "brand_color": data.get("brandColor", "#6366f1"),
            "accent_color": data.get("accentColor", "#fbbf24"),
            "text_contrast": data.get("textContrast", "light"),
            "intent": intent,
            "prompt": prompt_package.get("prompt", ""),
            "negative_prompt": prompt_package.get("negative_prompt", ""),
            "brand_profile_found": bool(brand_profile),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse-intent")
async def parse_intent_endpoint(request: IntentRequest):
    try:
        intent = parse_intent(request.text, mode=request.mode)
        brand_profile = load_brand_memory(request.user_id)
        return {
            "intent": intent,
            "brand_profile": brand_profile,
            "brand_profile_found": bool(brand_profile),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/variant-choice")
async def log_variant_choice_endpoint(request: VariantChoiceRequest):
    try:
        log_variant_choice(request.user_id, request.chosen_variant, request.intent)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/brand-memory/{user_id}")
async def get_brand_memory(user_id: str):
    try:
        profile = load_brand_memory(user_id)
        return {"user_id": user_id, "profile": profile, "found": bool(profile)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/brand-memory/save")
async def save_brand_memory_endpoint(request: BrandMemorySaveRequest):
    try:
        saved = save_brand_memory(request.user_id, request.profile)
        return {"status": "ok", "profile": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refine-design")
async def refine_design(request: RefineDesignRequest):
    try:
        data = extract_business_details(request.prompt)
        intent = request.parsed_intent or parse_intent(request.prompt, mode="final")
        brand_profile = load_brand_memory(request.user_id)

        prompt_package = build_prompt_package(intent, data, brand_profile, source_text=request.prompt)
        refined_prompt = build_refinement_prompt(prompt_package.get("prompt", ""), request.refinement_command)
        prompt_package["prompt"] = refined_prompt

        generated_paths = generate_routed_designs(
            prompt_package=prompt_package,
            extracted_data=data,
            source_text=request.prompt,
            final_submission=True,
        )

        ui_data = _translate_for_overlay(data, request.overlay_lang)
        variants = []
        for i, p in enumerate(generated_paths):
            variants.append({
                "variant_id": "A" if i == 0 else f"V{i+1}",
                "image_url": f"http://127.0.0.1:8000/generations/{os.path.basename(p)}"
            })

        return {
            "image_url": variants[0]["image_url"] if variants else "",
            "variants": variants,
            "business_name": ui_data.get("businessName", ""),
            "tagline": ui_data.get("tagline", ""),
            "services": ui_data.get("services", []),
            "contact": ui_data.get("contact", ""),
            "cta": ui_data.get("cta", ""),
            "layout_type": data.get("layoutType", "elegant"),
            "brand_color": data.get("brandColor", "#6366f1"),
            "accent_color": data.get("accentColor", "#fbbf24"),
            "text_contrast": data.get("textContrast", "light"),
            "intent": intent,
            "prompt": refined_prompt,
            "negative_prompt": prompt_package.get("negative_prompt", ""),
            "brand_profile_found": bool(brand_profile),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
