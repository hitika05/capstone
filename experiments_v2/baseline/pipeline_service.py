import json
import os
import re
from typing import Dict, List, Optional

from services.ai_service import generate_image
from services.image_service import generate_pricing_image


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BRAND_MEMORY_PATH = os.path.join(ASSETS_DIR, "brand_memory.json")
FEEDBACK_LOG_PATH = os.path.join(ASSETS_DIR, "variant_feedback.jsonl")

os.makedirs(ASSETS_DIR, exist_ok=True)


DESIGN_TYPES = [
    "instagram_post",
    "logo",
    "festival_post",
    "banner",
    "price_list_flyer",
]


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _has_keyword(text: str, keyword: str) -> bool:
    """Match a keyword as a word so Hindi substrings do not create false intents."""
    return re.search(
        rf"(?<![\w\u0900-\u097f]){re.escape(keyword.lower())}(?![\w\u0900-\u097f])",
        text,
        re.IGNORECASE,
    ) is not None


def keyword_intent_parser(text: str) -> Dict:
    t = _normalize(text)

    if any(k in t for k in ["price", "rate", "menu", "mrp", "₹", "rs", "प्राइस", "रेट", "भाव"]):
        design_type = "price_list_flyer"
    elif any(k in t for k in ["logo", "लोगो"]):
        design_type = "logo"
    elif any(k in t for k in ["festival", "diwali", "holi", "eid", "ganpati", "नवरात्र", "त्योहार"]):
        design_type = "festival_post"
    elif any(k in t for k in ["banner", "होर्डिंग", "flex"]):
        design_type = "banner"
    else:
        design_type = "instagram_post"

    business = "general business"
    business_map = {
        "cake shop": ["cake", "bakery", "केक", "बेकरी", "pastry"],
        "tailor shop": ["tailor", "tailors", "tailoring", "sewing", "alteration", "silai", "टेलर", "टेलर्स", "दर्जी", "सिलाई", "अल्टरशन", "शिवण"],
        "clothing shop": ["cloth", "clothes", "garment", "कपड़े", "फैशन"],
        "utensils shop": ["bartan", "utensil", "kitchenware", "बर्तन", "स्टील"],
        "mobile shop": ["smartphone", "iphone", "android", "mobile shop", "mobile store", "mobile repair", "मोबाइल दुकान", "मोबाइल शॉप", "मोबाइल रिपेयर"],
        "yoga studio": ["yoga", "योग", "योगा", "meditation", "wellness", "yoga class", "yoga studio", "योगा क्लास", "योग स्टूडियो"],
        "beauty salon": ["salon", "beauty", "makeup", "ब्राइडल", "मेकअप", "ब्यूटी", "पार्लर", "सैलून", "सलून", "parlour", "parlor"],
    }
    # Specific salon cues must win over generic words such as "मोबाइल" in a phone label.
    ordered_businesses = ["beauty salon", "cake shop", "tailor shop", "clothing shop", "utensils shop", "mobile shop", "yoga studio"]
    for label in ordered_businesses:
        if any(_has_keyword(t, k) for k in business_map[label]):
            business = label
            break

    color = ""
    for c in ["pink", "blue", "red", "green", "gold", "purple", "black", "white", "गुलाबी", "नीला", "लाल", "हरा", "पिंक", "परपल", "बैंगनी", "सफेद"]:
        if c in t:
            color = c
            break

    color_alias_map = {
        "पिंक": "pink",
        "गुलाबी": "pink",
        "परपल": "purple",
        "बैंगनी": "purple",
        "नीला": "blue",
        "लाल": "red",
        "हरा": "green",
        "सफेद": "white",
    }
    color = color_alias_map.get(color, color)

    mood = "professional"
    if any(k in t for k in ["sweet", "cute", "elegant", "minimal", "luxury", "festive", "clean"]):
        mood = ", ".join([k for k in ["sweet", "elegant", "minimal", "luxury", "festive", "clean"] if k in t])

    action = "create"
    if any(k in t for k in ["update", "change", "refine", "edit", "बदल", "change this"]):
        action = "refine"

    return {
        "design_type": design_type,
        "business": business,
        "color": color,
        "mood": mood,
        "action": action,
        "parser_mode": "keyword",
    }


def multilingual_bert_parser(text: str) -> Dict:
    """Final parser: tries multilingual BERT zero-shot, falls back to keyword parser."""
    intent = keyword_intent_parser(text)
    intent["parser_mode"] = "keyword_fallback"

    # Optional local model path. If unavailable, we keep fallback for reliability.
    try:
        from transformers import pipeline

        candidate_labels = DESIGN_TYPES
        clf = pipeline(
            "zero-shot-classification",
            model=os.getenv("INTENT_MODEL_ID", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"),
        )
        result = clf(text, candidate_labels)
        if result and result.get("labels"):
            best = str(result["labels"][0]).strip().lower()
            if best in DESIGN_TYPES:
                intent["design_type"] = best
                intent["parser_mode"] = "multilingual_bert"
    except Exception:
        pass

    return intent


def parse_intent(text: str, mode: str = "review") -> Dict:
    if mode == "final":
        return multilingual_bert_parser(text)
    return keyword_intent_parser(text)


def _read_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_brand_memory(user_id: Optional[str]) -> Dict:
    """Firebase-style brand memory interface with local JSON fallback."""
    if not user_id:
        return {}

    # Optional Firestore read when available.
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
        if firebase_admin._apps:
            db = firestore.client()
            doc = db.collection("brand_memory").document(user_id).get()
            if doc.exists:
                return doc.to_dict() or {}
    except Exception:
        pass

    all_memory = _read_json(BRAND_MEMORY_PATH, {})
    return all_memory.get(user_id, {}) if isinstance(all_memory, dict) else {}


def save_brand_memory(user_id: Optional[str], profile: Dict) -> Dict:
    if not user_id:
        return {}

    clean_profile = {
        "business_name": str(profile.get("business_name", "")).strip(),
        "tagline": str(profile.get("tagline", "")).strip(),
        "brand_color": str(profile.get("brand_color", "")).strip(),
        "accent_color": str(profile.get("accent_color", "")).strip(),
        "style": str(profile.get("style", "")).strip(),
        "contact": str(profile.get("contact", "")).strip(),
    }

    # Optional Firestore write path.
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
        if firebase_admin._apps:
            db = firestore.client()
            db.collection("brand_memory").document(user_id).set(clean_profile, merge=True)
            return clean_profile
    except Exception:
        pass

    all_memory = _read_json(BRAND_MEMORY_PATH, {})
    if not isinstance(all_memory, dict):
        all_memory = {}
    existing = all_memory.get(user_id, {}) if isinstance(all_memory.get(user_id), dict) else {}
    existing.update({k: v for k, v in clean_profile.items() if v})
    all_memory[user_id] = existing
    _write_json(BRAND_MEMORY_PATH, all_memory)
    return existing


def build_prompt_package(intent: Dict, extracted_data: Dict, brand_profile: Optional[Dict] = None, source_text: str = "") -> Dict:
    brand_profile = brand_profile or {}

    design_type = intent.get("design_type", "instagram_post")
    business = intent.get("business") or extracted_data.get("businessName", "business")
    mood = intent.get("mood") or "professional"
    # Current prompt extraction should outrank stale brand memory for this generation.
    color = intent.get("color") or extracted_data.get("brandColor", "") or brand_profile.get("brand_color", "")

    business_name = brand_profile.get("business_name") or extracted_data.get("businessName", "")
    tagline = brand_profile.get("tagline") or extracted_data.get("tagline", "")
    constraints = _extract_visual_constraints(source_text)
    mandatory_bg_objects = _extract_background_objects(source_text)

    if design_type == "logo":
        template = (
            "A professional brand logo concept for {business}, clean vector style, "
            "simple geometry, high contrast, centered composition, {color_hint}, no text in image"
        )
    elif design_type == "festival_post":
        template = (
            "A festive social media campaign post for {business}, {mood} atmosphere, "
            "celebratory decorations, high quality, social media ready, {color_hint}, no text in image"
        )
    elif design_type == "banner":
        template = (
            "A modern wide promotional banner visual for {business}, {mood} look, cinematic lighting, "
            "strong focal subject, premium ad quality, {color_hint}, no text in image"
        )
    elif design_type == "price_list_flyer":
        template = "price_list_template"
    else:
        template = (
            "A professional Instagram post visual for {business}, {mood} aesthetic, "
            "centered layout with clean negative space for overlays, high quality, social media ready, {color_hint}, no text in image"
        )

    color_hint = f"soft {color} palette" if color else "balanced commercial color palette"
    prompt = template.format(business=business, mood=mood, color_hint=color_hint)

    # Add strong content constraints from extracted theme when available.
    visual_theme = extracted_data.get("visualTheme", "")
    if visual_theme and template != "price_list_template":
        prompt = f"{prompt}. Main visual subject: {visual_theme}."

    explicit_background_requested = bool(constraints.get("background") or mandatory_bg_objects)

    # Hard-set explicit background requests so they do not get lost as a weak style hint.
    if constraints.get("background"):
        prompt = (
            f"{prompt} Background must visibly be {constraints['background']} across the main canvas. "
            "Do not keep the backdrop plain, empty, or flat."
        )
    elif constraints.get("palette"):
        prompt = (
            f"{prompt} Background should clearly use a {constraints['palette']} canvas or gradient. "
            "Do not keep the backdrop plain, empty, or flat."
        )

    if mandatory_bg_objects:
        prompt = (
            f"{prompt} MANDATORY BACKGROUND ELEMENTS: {', '.join(mandatory_bg_objects)}. "
            "These elements must be clearly visible and prominent in the background composition; do not omit. "
            "Ensure a product-rich environment, not a plain gradient wall."
        )

        # Compose exact scene-level constraints for common user storytelling patterns.
        obj_set = {o.strip().lower() for o in mandatory_bg_objects}
        if {"child", "crowd", "cakes"}.issubset(obj_set):
            prompt = (
                f"{prompt} Scene composition must show a child clearly visible on or near a large decorated cake, "
                "with a visible crowd behind in the background. Do not replace this with generic bakery shelves-only scene."
            )

    # If the prompt mentions a background requirement, keep it out of the text overlay and into the image itself.
    if any(k in _normalize(source_text) for k in ["background", "bg", "backdrop", "पार्श्वभूमी", "पार्श्व", "बैकग्राउंड"]):
        prompt = f"{prompt} Avoid dark/black background unless explicitly requested."
    else:
        relatable_bg = _infer_relatable_background(business, source_text, visual_theme)
        prompt = f"{prompt} Background should be {relatable_bg}; avoid empty/plain dark canvas."

    negative_prompt = (
        "blurry, low quality, watermark, text, letters, words, distorted, unprofessional, "
        "dark, crowded, cluttered layout, noisy background"
    )

    if explicit_background_requested:
        # Do not conflict with user-requested objects by penalizing all background richness.
        negative_prompt = (
            "blurry, low quality, watermark, text, letters, words, distorted, unprofessional, "
            "plain empty background, object-less background, flat backdrop"
        )

    if constraints.get("palette"):
        negative_prompt = f"{negative_prompt}, black background, unrelated color palette"
    elif "black" not in _normalize(source_text):
        negative_prompt = f"{negative_prompt}, plain black background, empty background, blank backdrop"

    if mandatory_bg_objects:
        negative_prompt = f"{negative_prompt}, missing required background objects"

    business_ctx = _normalize(f"{business} {source_text} {visual_theme}")
    if any(k in business_ctx for k in ["yoga", "योग", "योगा", "meditation", "wellness"]):
        prompt = f"{prompt} Scene must remain clearly yoga/wellness themed and never look like corporate office or food advertisement."
        negative_prompt = f"{negative_prompt}, corporate office boardroom, formal business suit model, burger poster, fast-food ad, restaurant menu board"

    if any(k in business_ctx for k in ["beauty", "salon", "parlour", "parlor", "spa", "makeup", "ब्यूटी", "पार्लर", "सैलून", "सलून", "मेकअप"]):
        prompt = (
            f"{prompt} Scene must clearly be a beauty parlour/salon interior with vanity mirrors, makeup studio lights, beauty products and salon styling ambience. "
            "Do not generate residential house exteriors, apartment facades, office buildings, real-estate architecture, or generic modern homes."
        )
        if any(k in business_ctx for k in ["pink", "purple", "पिंक", "गुलाबी", "परपल", "बैंगनी"]):
            prompt = f"{prompt} Keep salon decor predominantly pink/purple with floral accents when flowers are requested."
        negative_prompt = (
            f"{negative_prompt}, house exterior, apartment building, villa facade, real estate property photo, architecture render, interior living room, bedroom, kitchen"
        )

    return {
        "design_type": design_type,
        "business_name": business_name,
        "tagline": tagline,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
    }


def _build_variant_prompts(prompt: str) -> List[str]:
    return [
        prompt,
        f"{prompt} Variant B with alternate composition, warmer color temperature, and slightly different camera angle.",
    ]


def _extract_visual_constraints(source_text: str) -> Dict[str, str]:
    text = _normalize(source_text)
    constraints = {
        "background": "",
        "palette": "",
    }

    if not text:
        return constraints

    def _condense_background(candidate: str) -> str:
        candidate = candidate.strip(" .,;:!\n\t")
        candidate = re.sub(r"^(with|having)\s+", "", candidate).strip()
        candidate = re.sub(r"^(contain|contains|including|include|add)\s+", "", candidate).strip()
        candidate = re.sub(r"^(में|mein|me|in)\s+", "", candidate).strip()
        candidate = re.sub(r"\s*(दिखना\s*चाहिए|दिखना|दिखे|होना\s*चाहिए|चाहिए|clearly\s*visible|visible)$", "", candidate).strip()
        for token in ["साफ साफ", "साफ", "स्पष्ट", "पर"]:
            candidate = candidate.replace(token, " ")
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if not candidate:
            return ""

        filler_phrases = [
            "mein ho", "me ho", "main ho", "mein", "main", "ho", "hona", "chahiye", "please", "kar do",
            "mein ho across", "in bg", "in background", "background mein"
        ]
        if candidate in filler_phrases:
            return ""

        color_names = ["green", "pink", "red", "blue", "yellow", "gold", "white", "black", "purple", "orange", "हरा", "गुलाबी", "लाल", "नीला", "पिंक", "परपल", "बैंगनी", "सफेद"]
        for color_name in color_names:
            if color_name in candidate:
                return f"solid {color_name} background"

        # Keep only the first short phrase fragment.
        for stop_word in [" and ", " aur ", " or ", " ho ", " hai ", " hona ", " should ", " to "]:
            if stop_word in candidate:
                candidate = candidate.split(stop_word, 1)[0].strip()

        if len(candidate) < 5 or candidate in filler_phrases:
            return ""
        return candidate

    # Strongly capture explicit background instructions first.
    background_patterns = [
        r"background\s+(?:should\s+be|should|to\s+be|as|like)?\s*([a-zA-Z\u0900-\u097F\s-]{3,80})",
        r"(?:bg|backdrop|पार्श्वभूमी|बैकग्राउंड)\s*[:=]?\s*([a-zA-Z\u0900-\u097F\s-]{3,80})",
    ]
    for pattern in background_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .,;:!\n\t")
            if candidate:
                constraints["background"] = _condense_background(candidate)
                break

    # If the user only gave a color, turn it into a canvas background hint.
    palette_map = [
        ("green", "green"),
        ("pink", "pink"),
        ("पिंक", "pink"),
        ("red", "red"),
        ("blue", "blue"),
        ("yellow", "yellow"),
        ("gold", "gold"),
        ("white", "white"),
        ("सफेद", "white"),
        ("black", "black"),
        ("purple", "purple"),
        ("परपल", "purple"),
        ("बैंगनी", "purple"),
        ("orange", "orange"),
        ("हरा", "green"),
        ("गुलाबी", "pink"),
        ("लाल", "red"),
        ("नीला", "blue"),
    ]
    for keyword, color_name in palette_map:
        if keyword in text:
            constraints["palette"] = color_name
            break

    return constraints


def _extract_background_objects(text: str) -> List[str]:
    """Extract user-requested objects that must appear in background."""
    src = _normalize(text)
    if not src:
        return []

    objects: List[str] = []

    # Generic command patterns like: add X in background / background mein X ho.
    patterns = [
        r"add\s+([a-z\s]{2,40})\s+in\s+(?:the\s+)?background",
        r"include\s+([a-z\s]{2,40})\s+in\s+(?:the\s+)?background",
        r"show\s+([a-z\s]{2,40})\s+in\s+(?:the\s+)?background",
        r"put\s+([a-z\s]{2,40})\s+in\s+(?:the\s+)?background",
        r"background\s+(?:with|having)\s+([a-z\s]{2,40})",
        r"background\s+(?:mein|me)\s+([a-z\s\u0900-\u097F]{2,90})\s+(?:ho|hona|chahiye)",
        r"(?:बैकग्राउंड|background)\s+में\s+([a-z\s\u0900-\u097F]{2,90})\s+(?:डालो|डालोना|हो|रखो|चाहिए|दिखना\s+चाहिए)",
        r"(?:पार्श्वभूमी|background)\s+मध्ये\s+([a-z\s\u0900-\u097F]{2,90})\s+(?:ठेवा|दाखवा|हवा)",
    ]

    keyword_object_map = {
        "mobile phones": ["mobile phone", "mobile phones", "smartphone", "smartphones", "phone", "phones", "मोबाइल", "मोबाईल"],
        "yoga mats": ["yoga mat", "yoga mats", "योगा मैट", "योग मॅट", "योग मैट"],
        "plants": ["plants", "plant", "indoor plants", "पौधे", "झाडे"],
        "flowers": ["flower", "flowers", "floral", "फूल", "फ्लॉवर", "फ्लावर", "गुलाब"],
        "balloons": ["balloon", "balloons", "गुब्बारे", "फुगे"],
        "bracelets": ["bracelet", "bracelets", "bangle", "bangles", "चूड़ी", "चूड़ियां", "बांगडी", "बांगड्या"],
        "jewelry": ["jewelry", "jewellery", "ornaments", "आभूषण", "दागिने"],
        "cakes": ["cake", "cakes", "केक", "केक्स", "pastry", "pastries", "पेस्ट्री"],
        "child": ["child", "kid", "kids", "boy", "girl", "बच्चा", "बच्चे", "लड़का", "लड़की", "मुलगा", "मुलगी"],
        "crowd": ["crowd", "people", "audience", "भीड़", "लोग", "लोक"],
    }

    def _extract_keyword_objects(value: str) -> List[str]:
        found: List[str] = []
        phrase = _normalize(value)
        for canonical, keys in keyword_object_map.items():
            if any(k in phrase for k in keys) and canonical not in found:
                found.append(canonical)
        return found

    def _clean_object_phrase(value: str) -> str:
        v = value.strip(" .,;:!\n\t")
        v = re.sub(r"\b(and|aur|or|with|ke|ki|ka|for|wala|wali|वाला|वाली|का|की|के)\b", " ", v)
        v = re.sub(r"\b(साफ|स्पष्ट|clear|clearly|दिखना|दिखे|visible|चाहिए|है|हो|रखो|दाखवा|ठेवा)\b", " ", v)
        v = re.sub(r"\b(पर|में|मध्ये|mein|me|on|in|shelf|shelves|शेल्फ)\b", " ", v)
        for token in ["दिखना चाहिए", "होना चाहिए", "दिखना", " साफ साफ ", " स्पष्ट "]:
            v = v.replace(token, " ")
        v = re.sub(r"\s+", " ", v).strip()
        if len(v) < 2:
            return ""

        # Keep short object nouns only; long sentence-like fragments are handled by keyword extraction.
        words = v.split()
        if len(words) > 4:
            return ""
        return v

    for pattern in patterns:
        m = re.search(pattern, src)
        if m:
            raw_value = m.group(1)
            for obj in _extract_keyword_objects(raw_value):
                if obj not in objects:
                    objects.append(obj)

            value = _clean_object_phrase(raw_value)
            if value and value not in objects:
                objects.append(value)

    # Domain-specific quick detections for stronger recall.
    has_background_context = any(k in src for k in ["background", "bg", "mein", "बैकग्राउंड", "पार्श्वभूमी", "पीछे", "मागे", "behind", "backdrop"])
    for canonical, keys in keyword_object_map.items():
        if any(k in src for k in keys) and has_background_context:
            if canonical not in objects:
                objects.append(canonical)

    # De-duplicate and cap to avoid prompt bloat.
    return objects[:3]


def _infer_relatable_background(business: str, source_text: str, visual_theme: str) -> str:
    context = _normalize(f"{business} {source_text} {visual_theme}")

    if any(k in context for k in ["yoga", "योग", "योगा", "meditation", "wellness", "yoga studio", "yoga class"]):
        return "a peaceful yoga studio with yoga mats, natural light, indoor plants, and calm wellness atmosphere"
    if any(k in context for k in ["mobile", "smartphone", "repair", "मोबाइल", "मोबाईल", "phone repair", "electronics"]):
        return "a modern mobile repair store interior with illuminated shelves, phone accessories, and visible smartphones in the background"
    if any(k in context for k in ["cake", "bakery", "pastry", "केक", "बेकरी"]):
        return "a premium bakery interior with cake display counters and warm ambient lighting"
    if any(k in context for k in ["utensil", "bartan", "kitchenware", "बर्तन", "स्टील"]):
        return "a clean utensils showroom with organized stainless-steel product shelves"
    if any(k in context for k in ["clothing", "garment", "fashion", "कपड़े", "ड्रेस"]):
        return "a stylish clothing boutique interior with garment racks and soft retail lighting"
    if any(k in context for k in ["salon", "beauty", "makeup", "ब्राइडल", "मेकअप"]):
        return "an elegant beauty studio interior with mirrors and vanity lights"

    return "a professional commercial store interior relevant to the business type"


def build_refinement_prompt(base_prompt: str, refinement_command: str) -> str:
    cmd = _normalize(refinement_command)
    if not cmd:
        return base_prompt

    instructions = []
    if any(k in cmd for k in ["background", "bg", "पार्श्व", "बैकग्राउंड", "पार्श्वभूमी", "badal", "change background"]):
        instructions.append("Update the background style while preserving business subject and composition quality")
    if any(k in cmd for k in ["logo", "लोगो", "motha", "big", "large"]):
        instructions.append("Reserve cleaner focal space for a larger logo placement")
    if any(k in cmd for k in ["font", "टेक्स्ट", "मजकूर", "text"]):
        instructions.append("Keep stronger negative space and contrast for text overlay readability")
    if any(k in cmd for k in ["bright", "lighter", "चमक", "उजळ", "light"]):
        instructions.append("Use brighter lighting and uplifting color temperature")
    if any(k in cmd for k in ["dark", "moody", "गडद"]):
        instructions.append("Use a richer dark cinematic mood while retaining subject clarity")

    add_words = ["add", "include", "show", "put", "डाल", "जोड़", "add in", "with"]
    mobile_words = ["mobile", "mobiles", "smartphone", "smartphones", "phone", "phones", "मोबाइल", "मोबाईल"]
    if any(w in cmd for w in add_words) and any(w in cmd for w in mobile_words):
        instructions.append("Add clearly visible smartphones/mobile phones in the background display area")

    product_patterns = [
        r"add\s+([a-z\s]{3,30})\s+in\s+(?:the\s+)?background",
        r"include\s+([a-z\s]{3,30})\s+in\s+(?:the\s+)?background",
    ]
    for pattern in product_patterns:
        match = re.search(pattern, cmd)
        if match:
            obj = match.group(1).strip()
            if obj and "mobile" not in obj and "phone" not in obj:
                instructions.append(f"Add visible {obj} elements in the background")
            break

    strict_objects = _extract_background_objects(refinement_command)
    if strict_objects:
        instructions.append(
            f"MANDATORY background objects after refinement: {', '.join(strict_objects)}; these must be clearly visible"
        )

    if not instructions:
        instructions.append(f"Refinement requested by user: {refinement_command}")

    return f"{base_prompt}. Refinement constraints: {'; '.join(instructions)}."


def generate_routed_designs(
    prompt_package: Dict,
    extracted_data: Dict,
    source_text: str,
    final_submission: bool = False,
) -> List[str]:
    design_type = prompt_package.get("design_type", "instagram_post")

    if design_type == "price_list_flyer":
        business_name = extracted_data.get("businessName", "Price List")
        return [generate_pricing_image(source_text, business_name)]

    prompts = _build_variant_prompts(prompt_package["prompt"]) if final_submission else [prompt_package["prompt"]]
    negative_prompt = prompt_package.get("negative_prompt", "")
    return [generate_image(p, negative_prompt=negative_prompt) for p in prompts]


def log_variant_choice(user_id: Optional[str], chosen_variant: str, intent: Dict) -> None:
    if not user_id:
        return
    record = {
        "user_id": user_id,
        "chosen_variant": chosen_variant,
        "intent": intent,
    }
    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
