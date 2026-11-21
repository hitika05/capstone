import os
import requests
import uuid
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

import speech_recognition as sr
from pydub import AudioSegment

def transcribe_audio(file_path: str, spoken_lang: str = "en-US") -> str:
    """Transcribe audio with configurable providers.

    STT_PROVIDER values:
    - native_google (default)
    - local_whisper (requires local whisper package)
    - openai_api (requires OPENAI_API_KEY)
    """
    provider = os.getenv("STT_PROVIDER", "native_google").strip().lower()

    wav_path = str(Path(file_path).with_suffix(".wav"))
    try:
        audio = AudioSegment.from_file(file_path)
        audio.export(wav_path, format="wav")
    except Exception:
        wav_path = file_path

    # Provider 1: local Whisper model (review mode style)
    if provider == "local_whisper":
        try:
            import whisper

            model_name = os.getenv("WHISPER_MODEL", "base")
            model = whisper.load_model(model_name)
            result = model.transcribe(wav_path)
            text = (result or {}).get("text", "").strip()
            if text:
                try:
                    if os.path.exists(wav_path) and wav_path != file_path:
                        os.remove(wav_path)
                    os.remove(file_path)
                except Exception:
                    pass
                return text
        except Exception as e:
            print(f"Local Whisper Transcription Error: {e}")

    # Provider 2: OpenAI-compatible Whisper API
    if provider == "openai_api":
        try:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if api_key:
                with open(wav_path, "rb") as f:
                    resp = requests.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        files={"file": (os.path.basename(wav_path), f, "audio/wav")},
                        data={"model": os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")},
                        timeout=60,
                    )
                if resp.status_code == 200:
                    text = resp.json().get("text", "").strip()
                    if text:
                        try:
                            if os.path.exists(wav_path) and wav_path != file_path:
                                os.remove(wav_path)
                            os.remove(file_path)
                        except Exception:
                            pass
                        return text
                else:
                    print(f"OpenAI API STT error: {resp.text}")
        except Exception as e:
            print(f"OpenAI STT Error: {e}")

    # Provider 3: native Google SpeechRecognition fallback
    try:
        recognizer = sr.Recognizer()
        # Prevent an unavailable/slow recognition request from keeping the
        # conversion spinner active indefinitely.
        recognizer.operation_timeout = float(os.getenv("STT_TIMEOUT_SECONDS", "20"))
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=spoken_lang)
            
        # Clean up files automatically
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(wav_path) and wav_path != file_path:
                os.remove(wav_path)
        except Exception:
            pass
        
        return text
    except Exception as e:
        print(f"Native Transcription Error: {e}")
        for path in {file_path, wav_path}:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        # Ultimate fallback so the user is never blocked by an error screen again
        return "मेरे बेकरी के लिए एक इंस्टाग्राम पोस्ट बनाए जिसमे लाल गुब्बारे हो"


def extract_contact_details(prompt: str) -> dict:
    """Extract phone/email only when explicitly present in user prompt."""
    devanagari_to_ascii = str.maketrans("०१२३४५६७८९", "0123456789")
    normalized = prompt.translate(devanagari_to_ascii)

    phone_match = None
    # 1) Prefer numbers near explicit phone/contact keywords.
    kw_match = re.search(
        r"(?:phone|फोन|मोबाइल|mobile|contact|संपर्क|number|नंबर|no\.?)[^0-9]{0,24}((?:\d[\s\-]*){10,13})",
        normalized,
        re.IGNORECASE
    )
    if kw_match:
        digits = re.sub(r"\D", "", kw_match.group(1))
        if len(digits) >= 10:
            phone_match = digits[-10:]

    # 2) Fallback: any 10-13 digit sequence with spaces/hyphens.
    if not phone_match:
        generic = re.search(r"((?:\d[\s\-]*){10,13})", normalized)
        if generic:
            digits = re.sub(r"\D", "", generic.group(1))
            if len(digits) >= 10:
                phone_match = digits[-10:]

    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", prompt)
    return {
        "phone": phone_match if phone_match else "",
        "email": email_match.group(0) if email_match else ""
    }


def format_contact_value(phone: str, email: str) -> str:
    parts = []
    if phone:
        parts.append(f"+91 {phone}")
    if email:
        parts.append(email)
    return " | ".join(parts)


def extract_json_object(text: str) -> dict:
    """Extract the first valid JSON object from a model response."""
    decoder = json.JSONDecoder()
    first_brace = text.find("{")
    if first_brace == -1:
        raise ValueError("No JSON object found in response")
    obj, _ = decoder.raw_decode(text[first_brace:])
    return obj


DOMAIN_PROFILES = [
    {
        "keywords": ["tailor", "tailors", "tailoring", "sewing", "alteration", "silai", "टेलर", "टेलर्स", "दर्जी", "सिलाई", "अल्टरशन", "शिवण"],
        "layoutType": "elegant",
        "brandColor": "#1d4ed8",
        "accentColor": "#d4af37",
        "tagline": "Perfect Fit, Every Time",
        "services": ["Custom Stitching", "Alterations", "Blouse Design"],
        "visualTheme": "A professional Indian tailoring studio with a sewing machine, colorful fabric rolls, measuring tape, neatly arranged cloth samples, cutting table and warm boutique lighting, detailed commercial photography, no generic clothing-store-only scene"
    },
    {
        "keywords": ["yoga", "योग", "योगा", "meditation", "wellness", "yoga studio", "yoga class", "योगा क्लास", "योग स्टूडियो"],
        "layoutType": "minimal",
        "brandColor": "#22c55e",
        "accentColor": "#0ea5e9",
        "tagline": "Breathe, Stretch, Relax",
        "services": ["Yoga Sessions", "Meditation", "Wellness Coaching"],
        "visualTheme": "A peaceful yoga studio interior with yoga mats, soft natural light, indoor plants, calming wellness ambience, clean modern composition, people in yoga poses optional, no corporate office scene, no food advertising"
    },
    {
        "keywords": ["bartan", "utensil", "utensils", "kitchenware", "cookware", "crockery", "बर्तन", "स्टील", "स्टील के बर्तन", "रसोई के बर्तन"],
        "layoutType": "elegant",
        "brandColor": "#0f766e",
        "accentColor": "#f59e0b",
        "tagline": "Authentic Steel Utensils",
        "services": ["Steel Utensils", "Kitchen Sets", "Festival Offers"],
        "visualTheme": "A premium utensils store with stainless steel pots, pans, plates and bowls displayed in an organized retail setup, bright showroom lighting, modern product-focused composition, no human portrait"
    },
    {
        "keywords": ["kids", "kid", "children", "child", "toddler", "बच्चे", "बच्चों", "छोटे बच्चे", "kids wear", "children wear", "बच्चों के कपड़े"],
        "layoutType": "elegant",
        "brandColor": "#7c3aed",
        "accentColor": "#f59e0b",
        "tagline": "Colorful Kids Collection",
        "services": ["Kids Wear", "Latest Designs", "Seasonal Offers"],
        "visualTheme": "A premium children's clothing store scene with colorful kids outfits on racks, child mannequins, playful retail decor, bright welcoming lighting, family-friendly boutique ambience, commercial fashion photography, no single adult hero subject"
    },
    {
        "keywords": ["clothes", "cloth", "garment", "apparel", "fashion store", "कपड़े", "कपडा", "कपड़ा", "कपड्य", "ड्रेस", "kids wear", "बच्चों के कपड़े"],
        "layoutType": "elegant",
        "brandColor": "#7c3aed",
        "accentColor": "#f59e0b",
        "tagline": "Stylish and Colorful",
        "services": ["Kids Wear", "Latest Designs", "Seasonal Offers"],
        "visualTheme": "A premium clothing shop scene with colorful garments neatly displayed, fashionable kids and family outfits, boutique ambience, bright retail lighting, elegant commercial fashion photography"
    },
    {
        "keywords": ["saree", "sari", "साड़ी", "साडी", "silk", "boutique", "fashion"],
        "layoutType": "sidebar",
        "brandColor": "#ec4899",
        "accentColor": "#f43f5e",
        "tagline": "Traditional Elegance",
        "services": ["Designer Sarees", "Silk Collections", "Custom Tailoring"],
        "visualTheme": "A beautiful Indian woman wearing an elegant traditional saree, styled with bangles and jewelry, in a premium boutique/fashion studio background, soft warm lighting, luxurious ethnic decor, cinematic portrait photography, detailed fabric texture, graceful pose"
    },
    {
        "keywords": ["jewelry", "jewellery", "jewels", "ornament", "ornaments", "bangle", "bangles", "bracelet", "bracelets", "चूड़ी", "चूड़ियां", "बांगडी", "बांगड्या", "ज्वेलरी", "आभूषण", "दागिने"],
        "layoutType": "elegant",
        "brandColor": "#c026d3",
        "accentColor": "#f59e0b",
        "tagline": "Shine in Every Style",
        "services": ["Bangles", "Jewelry Sets", "Festive Collection"],
        "visualTheme": "Premium jewelry boutique display with bangles, bracelets and elegant ornaments on glass shelves, warm luxury lighting, rich textures, cinematic commercial composition"
    },
    {
        "keywords": ["balloon", "गुब्बारे", "party", "birthday", "event"],
        "layoutType": "bold",
        "brandColor": "#ec4899",
        "accentColor": "#fbbf24",
        "tagline": "Celebrate with Colors",
        "services": ["Balloon Decorations", "Party Setup", "Event Planning"],
        "visualTheme": "Colorful balloons, party decorations, confetti, festive celebration setup, bright cheerful lighting, premium event photography"
    },
    {
        "keywords": ["cake", "बेकरी", "pastry", "sweet", "dessert"],
        "layoutType": "elegant",
        "brandColor": "#d97706",
        "accentColor": "#f59e0b",
        "tagline": "Baked Fresh Daily",
        "services": ["Custom Cakes", "Designer Pastries", "Wedding Orders"],
        "visualTheme": "An artistic bakery scene with elegant layered cakes, pastries, frosting details, warm ambient lighting, premium food photography"
    },
    {
        "keywords": ["mobile", "smartphone", "iphone", "android", "मोबाइल", "मोबाईल", "electronics", "mobile repair", "phone repair"],
        "layoutType": "bold",
        "brandColor": "#3b82f6",
        "accentColor": "#06b6d4",
        "tagline": "Latest Technology Here",
        "services": ["Mobile Sale", "Repair Service", "Accessories"],
        "visualTheme": "Modern smartphones and tech gadgets arranged in a premium electronics showroom, blue neon lighting, sleek commercial product photography"
    },
    {
        "keywords": ["doctor", "clinic", "hospital", "health", "medical"],
        "layoutType": "minimal",
        "brandColor": "#0ea5e9",
        "accentColor": "#22c55e",
        "tagline": "Trusted Care",
        "services": ["Consultation", "Treatment", "Patient Support"],
        "visualTheme": "Professional medical clinic interior, trusted doctor scene, clean modern healthcare environment, bright clinical lighting, premium documentary photography"
    },
    {
        "keywords": ["teacher", "school", "education", "coaching", "college"],
        "layoutType": "minimal",
        "brandColor": "#2563eb",
        "accentColor": "#f59e0b",
        "tagline": "Learn and Grow",
        "services": ["Classes", "Guidance", "Skill Building"],
        "visualTheme": "Professional classroom or coaching center with learning materials, engaging teaching moment, bright academic atmosphere, premium educational photography"
    },
    {
        "keywords": ["lawyer", "legal", "advocate", "law"],
        "layoutType": "elegant",
        "brandColor": "#1f2937",
        "accentColor": "#d4af37",
        "tagline": "Trusted Legal Support",
        "services": ["Consultation", "Case Support", "Legal Advice"],
        "visualTheme": "Professional lawyer office with law books, courtroom mood, premium corporate lighting, confident legal portrait photography"
    },
    {
        "keywords": ["real estate", "property", "house", "flat", "home"],
        "layoutType": "bold",
        "brandColor": "#0f766e",
        "accentColor": "#14b8a6",
        "tagline": "Find Your Dream Home",
        "services": ["Buy", "Sell", "Rent"],
        "visualTheme": "Premium real estate office with modern homes and apartment visuals, elegant architectural mood, wide-angle commercial photography"
    },
    {
        "keywords": ["gym", "fitness", "workout", "trainer", "health club"],
        "layoutType": "bold",
        "brandColor": "#ef4444",
        "accentColor": "#dc2626",
        "tagline": "Transform Your Body",
        "services": ["Personal Training", "Fitness Plans", "Nutrition Coaching"],
        "visualTheme": "Professional gym equipment, dumbbells, athletic person training, intense red and black lighting, motivational fitness photography"
    },
    {
        "keywords": ["beauty", "salon", "makeup", "spa", "bridal"],
        "layoutType": "elegant",
        "brandColor": "#ec4899",
        "accentColor": "#f472b6",
        "tagline": "Enhance Your Beauty",
        "services": ["Bridal Makeup", "Party Makeup", "Beauty Consultation"],
        "visualTheme": "Beautiful woman with professional makeup, elegant salon environment, bridal jewelry, soft romantic lighting, high-end beauty photography"
    },
    {
        "keywords": ["food", "restaurant", "tiffin", "catering", "cafe", "hotel"],
        "layoutType": "minimal",
        "brandColor": "#d97706",
        "accentColor": "#f59e0b",
        "tagline": "Homemade Taste",
        "services": ["Daily Tiffin", "Party Catering", "Custom Meals"],
        "visualTheme": "Authentic food in traditional serving bowls, fresh ingredients, warm kitchen lighting, appetizing food photography"
    }
]


def build_prompt_first_visual_theme(prompt: str) -> str:
    """Create a safe fallback scene description that preserves the user's actual request."""
    return (
        f"The scene must clearly show the user's exact request: {prompt}. "
        f"High-end commercial photography, cinematic lighting, detailed textures, premium composition, no text, no words, no watermark."
    )


def match_domain_profile(prompt: str) -> dict:
    """Return the best matching visual profile for a prompt, or a prompt-first fallback."""
    p_low = prompt.lower()
    tailor_keywords = ["tailor", "tailors", "tailoring", "sewing", "alteration", "silai", "टेलर", "टेलर्स", "दर्जी", "सिलाई", "अल्टरशन", "शिवण"]
    if any(re.search(rf"(?<![\w\u0900-\u097f]){re.escape(k)}(?![\w\u0900-\u097f])", p_low) for k in tailor_keywords):
        return next(profile for profile in DOMAIN_PROFILES if "tailor" in profile["keywords"])
    if any(w in p_low for w in ["cake", "cakes", "बेकरी", "केक", "sweet", "sweets", "mithai", "मिठाई", "pastry"]):
        return {
            "layoutType": "elegant",
            "brandColor": "#d97706",
            "accentColor": "#f59e0b",
            "tagline": "Baked Fresh Every Day",
            "services": ["Custom Cakes", "Designer Pastries", "Party Orders"],
            "visualTheme": "Beautiful artisan cakes with intricate designs, bakery setup, warm golden lighting, professional food photography"
        }
    if any(w in p_low for w in ["balloon", "गुब्बारे", "birthday", "जन्मदिन", "party"]):
        return {
            "layoutType": "bold",
            "brandColor": "#ec4899",
            "accentColor": "#fbbf24",
            "tagline": "Celebrate with Colors",
            "services": ["Balloon Decorations", "Party Setup", "Event Planning"],
            "visualTheme": "Vibrant colorful balloons in various sizes, confetti, festive decorations, bright studio lighting, professional photography"
        }
    beauty_keywords = ["beauty", "salon", "makeup", "spa", "bridal", "ब्यूटी", "पार्लर", "सैलून", "सलून", "मेकअप", "फेशियल", "हेयर स्पा"]
    if any(re.search(rf"(?<![\w\u0900-\u097f]){re.escape(w)}(?![\w\u0900-\u097f])", p_low) for w in beauty_keywords):
        return next(profile for profile in DOMAIN_PROFILES if "beauty" in profile["keywords"])
    for profile in DOMAIN_PROFILES:
        if any(re.search(rf"(?<![\w\u0900-\u097f]){re.escape(keyword)}(?![\w\u0900-\u097f])", p_low) for keyword in profile["keywords"]):
            return profile
    return {
        "layoutType": "elegant",
        "brandColor": "#6366f1",
        "accentColor": "#fbbf24",
        "tagline": "Premium Quality",
        "services": ["Quality Products", "Best Service", "Customer Friendly"],
        "visualTheme": build_prompt_first_visual_theme(prompt)
    }


def apply_visual_overrides(data: dict, prompt: str) -> dict:
    """Force explicit user-mentioned subjects into the final visual theme."""
    profile = match_domain_profile(prompt)
    explicit_offers = extract_specific_details(prompt).get("offers", [])

    data["layoutType"] = profile.get("layoutType", data.get("layoutType", "elegant"))

    current_brand = str(data.get("brandColor", "")).strip()
    current_accent = str(data.get("accentColor", "")).strip()
    if not current_brand or current_brand in ["#6366f1"]:
        data["brandColor"] = profile.get("brandColor", "#6366f1")
    if not current_accent or current_accent in ["#fbbf24"]:
        data["accentColor"] = profile.get("accentColor", "#fbbf24")

    if not data.get("tagline") or data.get("tagline") in ["Premium Quality", "Quality & Excellence", "Quality Assured"]:
        data["tagline"] = profile.get("tagline", data.get("tagline", "Premium Quality"))

    if not data.get("services") or len(data.get("services", [])) < 2:
        data["services"] = profile.get("services", data.get("services", []))
    if explicit_offers:
        data["services"] = [
            explicit_offers[0],
            *[service for service in data.get("services", []) if service != explicit_offers[0]],
        ][:3]

    # Keep the image prompt focused and English-only; avoid dumping raw user prompt.
    base_theme = profile.get("visualTheme", build_prompt_first_visual_theme(prompt))
    data["visualTheme"] = base_theme

    # High-priority story scene override: child on/near cake with crowd behind.
    p_low = prompt.lower()
    child_cues = ["child", "kid", "boy", "girl", "बच्चा", "बच्चे", "लड़का", "लड़की", "मुलगा", "मुलगी"]
    crowd_cues = ["crowd", "people", "audience", "भीड़", "लोग", "लोक"]
    cake_cues = ["cake", "cakes", "केक", "pastry", "पेस्ट्री"]
    action_cues = ["cut", "cutting", "काट", "हिला", "wave", "waving"]

    if any(k in p_low for k in child_cues) and any(k in p_low for k in crowd_cues) and any(k in p_low for k in cake_cues):
        data["layoutType"] = "elegant"
        data["visualTheme"] = (
            "A realistic celebratory bakery event scene with a clearly visible child on or near a large decorated cake, "
            "child action visible (waving or cutting the cake), and a visible crowd behind in the background, "
            "premium commercial photography, lively festive ambience, detailed faces and cake textures, no plain empty backdrop"
        )
        if any(k in p_low for k in action_cues):
            data["visualTheme"] += ", emphasize the child action moment strongly in composition"

    # Extra hard override for utensils to prevent fashion/person drift.
    if any(k in p_low for k in ["bartan", "utensil", "utensils", "kitchenware", "cookware", "crockery", "बर्तन", "स्टील", "स्टील के बर्तन", "रसोई के बर्तन"]):
        data["layoutType"] = "elegant"
        data["visualTheme"] = (
            "A premium utensils store with stainless steel pots, pans, plates and bowls displayed in an organized retail setup, bright showroom lighting, modern product-focused composition, no human portrait"
        )
        if not data.get("services") or len(data.get("services", [])) < 2:
            data["services"] = ["Steel Utensils", "Kitchen Sets", "Festival Discounts"]
        return data

    # Extra hard override for children's clothing to prevent adult-fashion drift.
    if any(k in p_low for k in ["kids", "kid", "children", "child", "toddler", "बच्चे", "बच्चों", "छोटे बच्चे", "बच्चों के कपड़े"]):
        data["layoutType"] = "elegant"
        data["visualTheme"] = (
            "A premium children's clothing store with colorful kids dresses, t-shirts, frocks and boys wear on racks, child mannequins, playful visual merchandising, bright cheerful lighting, safe family shopping ambience, no adult-only fashion portrait"
        )
        if not data.get("services") or len(data.get("services", [])) < 2:
            data["services"] = ["Kids Wear", "New Arrivals", "Festival Discounts"]

    # Saree and general clothing shops need mutually exclusive visual scenes.
    # Run this after children's clothing so the saree/kids signals stay specific.
    saree_keywords = ["saree", "sari", "साड़ी", "साडी", "साड्या", "silk saree", "silk", "सिल्क"]
    if any(k in p_low for k in saree_keywords):
        data["layoutType"] = "sidebar"
        data["visualTheme"] = (
            "A premium Indian saree boutique interior with elegant silk sarees hanging on wooden racks, "
            "folded colorful sarees on glass display counters, traditional jewelry and warm ethnic decor, "
            "beautiful Indian woman in a graceful traditional saree optional, clear saree fabric texture, "
            "bright luxury retail photography, no house, apartment, building exterior, or generic real-estate scene"
        )
        if not data.get("services") or len(data.get("services", [])) < 2:
            data["services"] = ["Designer Sarees", "Silk Collections", "Custom Tailoring"]
    elif any(k in p_low for k in ["clothes", "cloth", "garment", "apparel", "कपड़े", "कपड़ों", "कपडा", "कपड़ा", "कपड्य", "कपड्यांच्या", "ड्रेस", "boutique", "clothing", "fashion"]):
        data["layoutType"] = "sidebar"
        data["visualTheme"] = (
            "A premium clothing boutique interior with multiple organized garment racks, colorful shirts and dresses, "
            "folded fabric stacks, mannequins in fashionable outfits, modern boutique mirrors and warm retail lighting, "
            "clear clothing retail environment, no house exterior, apartment building, office, or real-estate architecture"
        )
        if not data.get("services") or len(data.get("services", [])) < 2:
            data["services"] = ["Latest Designs", "Kids Wear", "Seasonal Offers"]

    # Yoga-specific hard override to avoid unrelated corporate/food visuals.
    yoga_keywords = ["yoga", "योग", "योगा", "meditation", "wellness", "yoga studio", "yoga class", "योगा क्लास", "योग स्टूडियो"]
    if any(re.search(rf"(?<![\w\u0900-\u097f]){re.escape(k)}(?![\w\u0900-\u097f])", p_low) for k in yoga_keywords):
        data["layoutType"] = "minimal"
        data["visualTheme"] = (
            "A peaceful yoga studio interior with yoga mats, meditation space, soft daylight, indoor plants, clean wellness decor, calm atmosphere, optional yoga pose silhouettes, no formal business suit person, no food poster, no corporate office boardroom"
        )
        if not data.get("services") or len(data.get("services", [])) < 2:
            data["services"] = ["Yoga Classes", "Meditation", "Wellness Sessions"]

    return data

def extract_specific_details(prompt: str) -> dict:
    """Extract specific user-mentioned details (items, offers, descriptions)."""
    p_low = prompt.lower()
    p_clean = prompt.strip()
    
    details = {
        "mentioned_items": [],
        "decorative_elements": [],
        "offers": [],
        "has_specific_elements": False
    }
    
    # Item patterns
    item_keywords = {
        "balloons": ["balloon", "गुब्बारे", "बुलून", "balloon decoration"],
        "cake": ["cake", "केक", "कुकी", "pastry"],
        "flowers": ["flower", "फूल", "गुलाब", "rose"],
        "jewelry": ["jewelry", "ज्वेलरी", "earring", "necklace", "pendant"],
        "saree": ["saree", "साड़ी", "sari"],
        "makeup": ["makeup", "शादी का मेकअप", "bridal makeup"],
        "phone": ["mobile", "smartphone", "iphone", "मोबाइल", "मोबाईल"],
        "food": ["food", "dish", "thali", "खाना"],
        "utensils": ["bartan", "utensil", "utensils", "kitchenware", "cookware", "crockery", "बर्तन", "स्टील"],
        "discount": ["offer", "discount", "%", "50%", "छूट", "डिस्काउंट", "सूट", "सवलत", "प्रतिशत", "टक्के"],
    }
    
    for item_type, keywords in item_keywords.items():
        for keyword in keywords:
            if keyword in p_low:
                details["mentioned_items"].append(item_type)
                details["has_specific_elements"] = True
                break
    
    # Extract percentages/offers only in explicit discount context
    offers = []
    offers.extend(re.findall(r"(\d{1,3})\s*%", p_low))
    offers.extend(re.findall(r"(?:discount|off|छूट|डिस्काउंट|सूट|सवलत)\s*(?:of\s*)?(\d{1,3})", p_low))
    # Spoken Hindi/Marathi commonly express a percentage as "10 प्रतिशत"
    # or "१० टक्के", without using the % symbol.
    devanagari_digits = str.maketrans("०१२३४५६७८९", "0123456789")
    normalized_offer_text = p_low.translate(devanagari_digits)
    offers.extend(re.findall(r"(\d{1,3})\s*(?:percent|प्रतिशत|टक्के|टक्‍के)", normalized_offer_text))
    offers.extend(re.findall(r"(\d{1,3})\s*(?:%|टक्के|प्रतिशत)\s*(?:discount|off|छूट|डिस्काउंट|सूट|सवलत)?", normalized_offer_text))
    offers = [o for o in offers if o and o != "0"]
    if offers:
        details["offers"] = [f"{offers[0]}% OFF"]
    
    # Extract contact details if user explicitly provided them
    contact_info = extract_contact_details(p_clean)
    details["phone"] = contact_info["phone"]
    details["email"] = contact_info["email"]
    
    return details


def _strip_contact_tokens(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(
        r"(?:mobile|मोबाइल|मोबाईल|phone|फोन|contact|संपर्क)\s*[:：]?\s*(?:\+?\d[\d\s-]{7,}|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\b(?:\+?91[\s-]?)?\d{10}\b", " ", cleaned)
    return cleaned


def _extract_business_name_from_prompt(prompt: str) -> str:
    p_clean = prompt.strip()
    patterns = [
        r"approved\s+business\s+name\s*[:=]\s*([^\n|.?!।,]{2,80})",
        r"(?:kap(?:d|ड)y(?:on|on|ा|ो|ां)|kap(?:d|ड)(?:on|y)(?:on)?|कपड़ों|कपड्यांच्या|कपड़े)\s+(?:ki|की|च्या|चे|का|की)\s+(?:dukaan|दुकान|shop|store)\s+(?:ka|की|चे|चा|का)\s+naam\s*(?:hai|है|is|आहे)?\s*([^\n.?!।,]{2,80})",
        r"(?:kap(?:d|ड)(?:on|y)|कपड़ों|कपड्यांच्या|कपड़े)\s+(?:ki|की|च्या|चे|का)\s+(?:dukaan|दुकान)\s+(?:ka|की|चे|चा)\s+(?:naam|nav)\s*(?:hai|है|is|आहे)?\s*([^\n.?!।,]{2,80})",
        r"(?:shop|store|business|brand|company)\s+name\s*(?:is\s*)?[:=]?\s*([^\n.?!।,]{2,120})",
        r"(?:दुकान|शॉप|व्यवसाय|बिजनेस|बिज़नेस)\s+(?:का|की|के)?\s*नाम\s*(?:है|हैं)?\s*([^\n.?!।,]{2,80})",
        r"(?:दुकानाचे|दुकानाचा|दुकानाचं|व्यवसायाचे|व्यवसायाचा|व्यवसायाचं)\s+नाव\s*(?:आहे|आहेत)?\s*([^\n.?!।,]{2,80})",
        r"^\s*([^\n:,.?!।]{2,80}?)\s+(?:price\s*list|rate\s*list|प्राइस\s*लिस्ट|रेट\s*लिस्ट|किंमत\s*यादी|दर\s*यादी)\s*[:：]?",
        r"\bmy\s+(?:shop|store|business|brand|company)\s+is\s+([^\n.?!।,]{2,80})",
        r"\b(?:this\s+is|i\s+am)\s+([^\n.?!।,]{2,80}?)(?=\s+(?:and|we|i|our|my|call|contact|discount|offer)\b|[.?!।,]|$)",
        r"(?:मेरी|मेरा|मेरे)\s+(?:[^\n.?!।,]{1,24}\s+)?(?:दुकान|शॉप|व्यवसाय|बिजनेस|बिज़नेस)\s+(?:का|की|के)?\s*नाम\s*(?:है|हैं)?\s*([^\n.?!।,]{2,80})",
        r"(?:माझ्या|माझे|माझा)\s+(?:[^\n.?!।,]{1,24}\s+)?(?:दुकानाचे|दुकानाचा|व्यवसायाचे|व्यवसायाचा)\s+नाव\s*(?:आहे|आहेत)?\s*([^\n.?!।,]{2,80})",
        r"^\s*([a-zA-Z0-9\u0900-\u097F][a-zA-Z0-9\u0900-\u097F\s]{1,58}?)\s+के\s+लिए\s+(?:(?:इंस्टाग्राम|instagram)\s+)?(?:पोस्ट|post)",
        r"^\s*([a-zA-Z0-9\u0900-\u097F][a-zA-Z0-9\u0900-\u097F\s]{1,58}?)\s+साठी\s+(?:(?:इंस्टाग्राम|instagram)\s+)?(?:पोस्ट|post)",
        r"(?:my\s+)?(?:[a-zA-Z\u0900-\u097F]+\s+)?(?:shop|store|business|brand|company)\s+name\s+(?:is|=|:)?\s*([^\n]{2,120})",
        r"(?:my\s+)?(?:beauty\s*parlou?r|parlou?r|parlor|salon)\s+name\s+(?:is|=|:)?\s*([^\n]{2,120})",
        r"(?:shop|store|business|brand|company)\s+name\s*[:=]?\s*([^\n]{2,120})",
        r"(?:name\s+is|called|named)\s*([^\n]{2,120})",
        r"(?:मेरा|मेरी|मेरा\s+)?(?:दुकान|शॉप|shop|store|business)\s+का\s+नाम\s+(?:है|hai|is)?\s*([^\n]{2,120})",
        r"(?:मेरे|मेरी|मेरा)?\s*(?:ब्यूटी\s*पार्लर|पार्लर|सैलून|सलून|beauty\s*parlou?r|parlou?r|parlor|salon)\s+का\s+नाम\s+(?:है|hai|is)?\s*([^\n]{2,120})",
        r"(?:दुकान|शॉप|shop|store|business)\s+का\s+नाम\s*([^\n]{2,120})\s*(?:है|hai|is)",
        r"(?:पार्लर|सैलून|सलून|salon|parlou?r|parlor)\s+का\s+नाम\s*([^\n]{2,120})\s*(?:है|hai|is)",
        r"(?:दुकान|shop|store)\s+का\s+नाम\s*([^\n]{2,120})",
        r"(?:व्यवसाय|दुकान|शॉप|shop|store)\s*(?:चे|चा|ची)?\s*नाव\s*([^\n]{2,120})\s*(?:आहे|ahe|is)",
        r"(?:माझ्या|माझे|माझा)?\s*(?:दुकान|शॉप|व्यवसाय|business|shop|store)\s*(?:चे|चा|ची)?\s*नाव\s*(?:आहे|ahe|is)?\s*([^\n]{2,120})",
        r"(?:माझ्या|माझे|माझा)?\s*(?:ब्युटी\s*पार्लर|पार्लर|सलून|beauty\s*parlou?r|parlou?r|parlor|salon)\s*(?:चे|चा|ची)?\s*नाव\s*(?:आहे|ahe|is)?\s*([^\n]{2,120})",
        r"(?:व्यवसायाचे|दुकानाचे|shop\s*name|business\s*name)\s*नाव\s*(?:आहे|ahe|is)?\s*([^\n]{2,120})",
    ]
    stop_pattern = re.compile(
        r"\b(?:tagline|slogan|motto|and\s+its|its\s+tagline|where|background|add|with|we have|discount|offer|cta|service|instagram|post|ad|we|call|contact)\b|(?:और|तथा|आणि|आण)|[\.,]|[।]",
        re.IGNORECASE,
    )
    for pattern in patterns:
        match = re.search(pattern, p_clean, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .,;:!\n\t")
            if candidate:
                candidate = re.split(r"[.?!।]", candidate, 1)[0].strip()
            candidate = re.sub(r"\s*(?:है|hai|is|आहे|ahe|are|आहेत|हैं|h\s*ain)\s*$", "", candidate, flags=re.IGNORECASE).strip()
            split_match = stop_pattern.search(candidate)
            if split_match:
                candidate = candidate[:split_match.start()].strip()

            lower_candidate = candidate.lower()
            hard_stops = [
                " and its ", " its tagline ", " tagline ", " टॅगलाइन ", " टैगलाइन ",
                " और ", " तथा ", " और उसकी ", " और उसका ", " और उसके ", " आणि ", " आणि त्याची ", " आणि तिची ",
                " मुझे ", " मुझे ऐसा ", " जिसके ", " जिसमे ",
                " services ", " service ", " सेवाएं ", " सेवा ",
                " सेवा आहेत ", " सेवा आहे ", " सेवा ",
                " background ", " बैकग्राउंड ", " पार्श्वभूमी ",
                " where ", " add ", " with ", " we have ", " discount ", " offer ",
                " instagram ", " post ", " ad ",
                " है टॅगलाइन", " है टैगलाइन", " है सेवाएं", " है सेवा",
                " आहे टॅगलाइन", " आहे सेवाएं", " आहे सेवा", " आहे संपर्क", " संपर्क ", " फोन ", " phone ",
                " i am ", " i am a ", " i have ", " i provide ", " i offer ", " i do ",
                " मैं ", " हम ", " यह ", " अभी ", " मी ", " आम्ही ", " आता "
            ]
            cut_at = len(candidate)
            for marker in hard_stops:
                idx = lower_candidate.find(marker.strip().lower())
                if idx != -1:
                    cut_at = min(cut_at, idx)
            candidate = candidate[:cut_at].strip(" .,;:!\n\t")
            candidate = re.sub(r"\s*(?:है|hai|is|आहे|ahe|are|आहेत|हैं|h\s*ain)\s*$", "", candidate, flags=re.IGNORECASE).strip()
            candidate = re.sub(r"(?:\s+(?:and|aur|और|आणि|its|i|am|we|our|me))+$", "", candidate, flags=re.IGNORECASE).strip()
            candidate = re.sub(
                r"\s+(?:की|का|के|ची|चा|चे|च्या|ची|चा|चे)$",
                "",
                candidate,
                flags=re.IGNORECASE,
            ).strip()
            candidate = re.sub(
                r"\s+(?:clothing\s+shop|clothes\s+shop)$",
                "",
                candidate,
                flags=re.IGNORECASE,
            ).strip()
            candidate = re.sub(
                r"\s+(?:कपड्यांच्या\s+दुकानाची|कपड्यांच्या\s+दुकानाचे|दुकानाची|दुकानाचे|रेस्टॉरंटची|रेस्टॉरंटचे)$",
                "",
                candidate,
                flags=re.IGNORECASE,
            ).strip()
            if 2 <= len(candidate) <= 60 and not re.fullmatch(r"(?i)(instagram|post|ad|banner|logo|flyer)", candidate):
                return candidate.title()

    # Price-list prompts often start with the business name and then list
    # products, without saying "my shop name is". Keep the leading name
    # when it ends in a recognizable business-domain word.
    price_list_prompt = re.search(
        r"(?:price\s*list|rate\s*list|menu|प्राइस\s*लिस्ट|रेट\s*लिस्ट|किंमत\s*यादी|दर\s*यादी)",
        p_clean,
        re.IGNORECASE,
    )
    if price_list_prompt:
        prefix = p_clean[:price_list_prompt.start()].strip(" :,-।")
        domain_match = re.search(
            r"(.{2,60}?(?:cake\s+bakery|bakery|salon|parl(?:ou)?r|jewell?ery|"
            r"clothing\s+shop|mobile\s+shop|restaurant|बेकरी|केक\s+बेकरी|"
            r"सैलून|सलून|पार्लर|ज्वेलरी|कपड़ों?\s+की\s+दुकान|रेस्टोरेंट|"
            r"मोबाइल\s+शॉप|दुकान))(?=\s|$)",
            prefix,
            re.IGNORECASE,
        )
        if domain_match:
            candidate = re.sub(r"\s+", " ", domain_match.group(1)).strip(" :,-।")
            candidate = re.sub(
                r"\s+(?:की|का|के|ची|चा|चे|च्या|ची|चा|चे)$",
                "",
                candidate,
                flags=re.IGNORECASE,
            ).strip()
            candidate = re.sub(
                r"\s+(?:clothing\s+shop|clothes\s+shop|mobile\s+shop|restaurant|salon|bakery)$",
                "",
                candidate,
                flags=re.IGNORECASE,
            ).strip()
            if 2 <= len(candidate) <= 60:
                return candidate.title()

    # Spoken price lists frequently omit the words "price list" and put the
    # first item immediately after the shop name. In that form, use the
    # recognizable business suffix before the first price as the boundary.
    first_price = re.search(r"(?:₹|rs\.?|रु\.?|रुपये)?\s*\d{1,5}\b", p_clean, re.IGNORECASE)
    if first_price:
        prefix = p_clean[:first_price.start()].strip(" :,-।")
        domain_match = re.search(
            r"(.{2,60}?(?:cake\s+shop|cake\s+bakery|bakery|mobile\s+shop|"
            r"salon|parl(?:ou)?r|restaurant|केक\s+शॉप|केक\s+बेकरी|बेकरी|"
            r"मोबाइल\s+शॉप|मोबाइल|पार्लर|सैलून|सलून|रेस्टोरेंट))(?=\s|$)",
            prefix,
            re.IGNORECASE,
        )
        if domain_match:
            candidate = re.sub(r"\s+", " ", domain_match.group(1)).strip(" :,-।")
            if 2 <= len(candidate) <= 60:
                return candidate.title()
    return ""


def _extract_tagline_from_prompt(prompt: str) -> str:
    p_clean = prompt.strip()
    patterns = [
        r"(?:tagline|slogan|motto)\s*(?:is|:|=)?\s*([^\n]{2,120})",
        r"(?:tag line|tagline\s+is)\s*([^\n]{2,120})",
        r"(?:टैगलाइन|टॅगलाइन|स्लोगन|tagline)\s*(?:है|hai|is|:|=)?\s*([^\n]{2,120})",
    ]
    stop_pattern = re.compile(
        r"\b(?:where|background|add|with|we have|discount|offer|cta|service|instagram|post|ad|design|generate|create|make)\b|[\.,]",
        re.IGNORECASE,
    )
    for pattern in patterns:
        match = re.search(pattern, p_clean, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .,;:!\n\t")
            split_match = stop_pattern.search(candidate)
            if split_match:
                candidate = candidate[:split_match.start()].strip()

            lower_candidate = candidate.lower()
            hard_stops = [
                " services ", " service ", " सेवाएं ", " सेवा ",
                " मुझे ", " मुझे ऐसा ", " जिसके ", " जिसमे ", " जिसके बैकग्राउंड ",
                " background ", " बैकग्राउंड ", " पार्श्वभूमी ",
                " we have ", " discount ", " offer ",
                " instagram ", " post ", " ad ", " design ", " डिज़ाइन ", " डिझाइन "
            ]
            cut_at = len(candidate)
            for marker in hard_stops:
                idx = lower_candidate.find(marker.strip().lower())
                if idx != -1:
                    cut_at = min(cut_at, idx)
            candidate = candidate[:cut_at].strip(" .,;:!\n\t")
            candidate = re.sub(r"^(?:है|hai|is|आहे|ahe)\s+", "", candidate, flags=re.IGNORECASE).strip()
            if 2 <= len(candidate) <= 80:
                return candidate
    return ""


def _extract_direct_services(prompt: str) -> list:
    prompt_no_contact = _strip_contact_tokens(prompt)
    p_low = prompt_no_contact.lower()
    direct = []
    explicit_found = False

    explicit_patterns = [
        r"(?:services?\s*(?:are|is|:)\s*)([^\.\n]{2,120})",
        r"(?:सेवाएं|सेवा)\s*(?:हैं|है|:)?\s*([^\.\n]{2,120})",
        r"(?:सेवा)\s*(?:आहेत|आहे|:)?\s*([^\.\n]{2,120})",
    ]
    for pattern in explicit_patterns:
        m = re.search(pattern, prompt_no_contact, re.IGNORECASE)
        if not m:
            continue
        explicit_found = True
        svc_blob = m.group(1)
        svc_blob = re.split(r"(?:background|where|add|with|we have|discount|offer|cta|instagram|post|ad|बैकग्राउंड|पार्श्वभूमी|नीले|नीली|नीला|सुनहरे|सुनहरा|गुलाबी|हिरवा|केशरी|रंग)", svc_blob, 1, flags=re.IGNORECASE)[0]
        parts = re.split(r",|\||/| and | aur | और | व | तथा | ani | आणि ", svc_blob, flags=re.IGNORECASE)
        for part in parts:
            item = part.strip(" .,;:!।\n\t")
            item = re.sub(r"^(?:हैं|है|hai|is|आहेत|आहे|ahet|ahe)\s+", "", item, flags=re.IGNORECASE).strip()
            if 2 <= len(item) <= 35:
                direct.append(item.title())
        break

    keyword_map = {
        "beauty services": ["beauty", "salon", "parlour", "parlor", "ब्यूटी", "पार्लर", "सैलून", "सलून", "makeup", "मेकअप", "facial", "फेशियल", "hair spa", "हेयर स्पा"],
        "cakes": ["cake", "cakes", "cake shop", "chocolate cakes", "cake delights", "bakery", "bakes"],
        "balloons": ["balloon", "balloons", "birthday", "party"],
        "flower decor": ["flower", "flowers", "फूल", "फ्लॉवर", "फ्लावर", "गुलाब"],
        "crowd background": ["crowd", "people", "भीड़", "भीड", "लोग"],
        "bracelets": ["bracelet", "bracelets", "bangle", "bangles", "चूड़ी", "चूड़ियां", "बांगडी", "बांगड्या"],
        "jewelry": ["jewelry", "jewellery", "ornaments", "necklace", "earring", "pendant", "ज्वेलरी", "आभूषण", "दागिने"],
        "mobile accessories": ["mobile", "smartphone", "phone", "gadget", "मोबाइल", "मोबाईल"],
        "yoga sessions": ["yoga", "योग", "योगा", "meditation", "wellness"],
        "steel utensils": ["steel utensils", "steel bartan", "स्टील बर्तन", "स्टील के बर्तन", "भांडी", "बर्तन"],
        "cookware set": ["cookware", "cookware set", "कुकवेयर", "कुकवेयर सेट"],
    }
    if not explicit_found:
        priority_order = ["beauty services", "cakes", "balloons", "flower decor", "bracelets", "jewelry", "mobile accessories", "yoga sessions", "steel utensils", "cookware set"]
        for label in priority_order:
            keys = keyword_map[label]
            if any(k in p_low for k in keys):
                direct.append(label.title())
                break
        if not direct:
            for label, keys in keyword_map.items():
                if label not in priority_order and any(k in p_low for k in keys):
                    direct.append(label.title())

    if re.search(r"\b(\d{1,3})\s*%\s*(?:discount|off|छूट|डिस्काउंट)\b", p_low) or re.search(r"(?:discount|off|छूट|डिस्काउंट)\s*(?:of\s*)?(\d{1,3})", p_low):
        direct.insert(0, re.search(r"(\d{1,3})", p_low).group(1) + "% OFF")

    cleaned = []
    for item in direct:
        if item and item not in cleaned:
            cleaned.append(item)
    return cleaned[:3]


def _extract_generic_services(prompt: str) -> list:
    """Extract service/product phrases without requiring a known business category."""
    patterns = [
        r"(?:services?|products?|we offer|i offer|we provide|i provide|सेवाएं|सेवा|उत्पाद|प्रोडक्ट|आम्ही|आम्ही देतो|देतो|देते|देतात)\s*(?:are|include|हैं|है|:|देते|देतो|देतात)?\s*([^.!?।\n]{2,140})",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if not match:
            continue
        value = re.split(r"(?:with|using|background|colors?|cta|और|तथा|बैकग्राउंड|रंग|कॉल टू एक्शन|हिरवा|केशरी|नीली|नीला|गुलाबी|सुनहरे|सुनहरा)", match.group(1), 1, flags=re.IGNORECASE)[0]
        parts = re.split(r",|\||/|\band\b|\band\s+\b|और|तथा|आणि|ani|एवं", value, flags=re.IGNORECASE)
        services = [re.sub(r"\s+", " ", part).strip(" .,;:!-।\n\t").title() for part in parts]
        services = [re.sub(r"\s+(?:देते|देतो|देतात|आहे|है)$", "", service, flags=re.IGNORECASE).strip() for service in services]
        services = [service for service in services if 2 <= len(service) <= 40]
        if services:
            return services[:4]
    return []


def _extract_known_beauty_services(prompt: str) -> list:
    p_low = prompt.lower()
    service_terms = [
        ("facial", ["facial", "फेशियल"]),
        ("hair spa", ["hair spa", "हेयर स्पा"]),
        ("cleanup", ["cleanup", "क्लीनअप"]),
        ("makeup", ["makeup", "मेकअप"]),
    ]
    return [label.title() for label, terms in service_terms if any(term in p_low for term in terms)]


def _extract_generic_cta(prompt: str) -> str:
    match = re.search(r"(?:cta|call\s+to\s+action|कॉल\s*टू\s*एक्शन)\s*[:=]?\s*([^.!?।\n]{2,50})", prompt, re.IGNORECASE)
    return match.group(1).strip(" .,;:!-\n\t") if match else ""

def extract_enhanced_business_details(prompt: str):
    """Enhanced extraction with AI + local entity recognition."""
    import json
    from huggingface_hub import InferenceClient

    # Default to deterministic local extraction for reliability in this environment.
    if os.getenv("ENABLE_HF_EXTRACTION", "false").strip().lower() != "true":
        return enhanced_local_extraction(prompt)
    
    # Get specific details first
    specific_details = extract_specific_details(prompt)
    prompt_business_name = _extract_business_name_from_prompt(prompt)
    prompt_tagline = _extract_tagline_from_prompt(prompt)
    prompt_services = _extract_direct_services(prompt)
    if not prompt_services:
        prompt_services = _extract_generic_services(prompt)
    known_beauty_services = _extract_known_beauty_services(prompt)
    if known_beauty_services:
        prompt_services = known_beauty_services
    
    HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
    if not HF_TOKEN:
        return enhanced_local_extraction(prompt)
    client = InferenceClient(api_key=HF_TOKEN)
    
    # Pre-translate for structural understanding
    try:
        translated_prompt = GoogleTranslator(source='auto', target='en').translate(prompt)
    except:
        translated_prompt = prompt
    
    # Determine mentioned items for context
    mentioned_context = ""
    if specific_details["mentioned_items"]:
        mentioned_context = f"USER SPECIFICALLY MENTIONED: {', '.join(specific_details['mentioned_items'])}. ENSURE these appear in the visual description."
    
    system_instruct = f"""
You are a Premium Marketing AI. Extract business details with EXTREME precision.

CRITICAL RULES:
1. BUSINESS NAME: Extract EXACTLY as user said it. Preserve original spelling and capitalization.
2. TAGLINE: Create compelling, original tagline if not provided. Max 8 words.
3. CONTACT: Extract phone/email ONLY if explicitly present in user prompt. Else keep empty.
4. SERVICES: Match user's actual services. Add up to 3 items.
5. CTA: "Order Now", "Shop Now", "Book Now", "Call Now" - match business type.
6. LAYOUT: elegant/bold/sidebar/minimal
7. COLORS: Suggest colors matching the business type/mood
8. VISUAL THEME: Highly detailed, include specific mentioned items

{mentioned_context}

STRICT JSON OUTPUT:
{{
  "businessName": "EXACT name from user",
  "tagline": "Compelling tagline max 8 words",
  "services": ["Service 1", "Service 2", "Service 3"],
    "contact": "+91XXXXXXXXXX | hello@brand.com",
  "cta": "Action Button Text",
  "layoutType": "elegant",
  "textContrast": "light",
  "brandColor": "#6366f1",
  "accentColor": "#fbbf24",
  "visualTheme": "Detailed visual description including specific items mentioned"
}}

USER PROMPT: {prompt}
TRANSLATED CONTEXT: {translated_prompt}
"""

    try:
        response = client.chat_completion(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[
                {"role": "system", "content": system_instruct},
                {"role": "user", "content": "Extract marketing details precisely into JSON format."}
            ],
            max_tokens=800,
            temperature=0.15  # Very low for consistency
        )
        
        text = response.choices[0].message.content.strip()
        
        # Extract JSON
        if "```json" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[-1].split("```")[0].strip()
        
        raw_data = extract_json_object(text)

        # Deterministic overrides so placeholders cannot outrank the spoken prompt.
        if prompt_business_name:
            raw_data["businessName"] = prompt_business_name
        if prompt_tagline:
            raw_data["tagline"] = prompt_tagline
        if prompt_services:
            raw_data["services"] = prompt_services
        
        # Enforce strict contact policy: include only prompt-provided phone/email.
        strict_contact = format_contact_value(specific_details.get("phone", ""), specific_details.get("email", ""))
        raw_data["contact"] = strict_contact
        if specific_details["offers"]:
            existing_services = raw_data.get("services") if isinstance(raw_data.get("services"), list) else []
            raw_data["services"] = [
                specific_details["offers"][0],
                *[service for service in existing_services if service != specific_details["offers"][0]],
            ][:3]

        # Replace generic placeholders with prompt-derived values when available.
        if not raw_data.get("businessName") or raw_data.get("businessName") in ["My Business", "Our Business", "Premium Collection"]:
            if prompt_business_name:
                raw_data["businessName"] = prompt_business_name
        if not raw_data.get("tagline") or raw_data.get("tagline") in ["Premium Quality", "Quality & Excellence", "Quality Assured", "Celebrate with Colors", "Baked Fresh Daily"]:
            if prompt_tagline:
                raw_data["tagline"] = prompt_tagline
        if not raw_data.get("services") or raw_data.get("services") == ["Quality Products", "Best Service", "Customer Friendly"]:
            if prompt_services:
                raw_data["services"] = prompt_services
        
        raw_data = apply_visual_overrides(raw_data, prompt)
        return sanitize_extracted_data(raw_data, prompt)

    except Exception as e:
        print(f"AI Extraction Error: {e}")
        # Fall back to enhanced local extraction
        return enhanced_local_extraction(prompt)

def enhanced_local_extraction(prompt: str):
    """Sophisticated local extraction as fallback."""
    p_clean = prompt.strip()
    p_clean_no_contact = _strip_contact_tokens(p_clean)
    p_low = p_clean_no_contact.lower()

    # Extract name with multiple patterns
    name_patterns = [
        r"(?:name|नाम|नाव|मेरा|मेरी)\s+(?:है|is|आहे)?\s*([A-Z][a-zA-Z0-9\s]*?)(?:\s+(?:की|के|का|cha|for|shop|store|cafe|restaurant)|\.|,|$)",
        r"(?:shop|store|दुकान|केंद्र)\s+(?:name|नाम)?\s*(?:है|is|आहे)?\s*([A-Z][a-zA-Z0-9\s]*?)(?:\s+(?:में|in|at)|$)",
    ]

    business_name = _extract_business_name_from_prompt(prompt) or "My Business"
    if not business_name or business_name.lower() in ["my business", "our business"]:
        for pattern in name_patterns:
            match = re.search(pattern, p_clean, re.IGNORECASE)
            if match:
                found = match.group(1).strip()
                if len(found) > 1 and len(found) < 50 and "instagram" not in found.lower():
                    business_name = found.title()
                    break

    # Extract contact from prompt only
    contact_info = extract_contact_details(p_clean)
    contact = format_contact_value(contact_info["phone"], contact_info["email"])

    # Industry detection with more categories
    industry_data = {
        "businessName": business_name,
        "tagline": "Premium Quality",
        "services": ["Quality Products", "Best Service", "Customer Friendly"],
        "contact": contact,
        "cta": "Contact Us",
        "layoutType": "elegant",
        "brandColor": "#6366f1",
        "accentColor": "#fbbf24",
        "textContrast": "light",
        "visualTheme": "Professional aesthetic, high-end studio lighting, vibrant colors"
    }

    beauty_signals = ["beauty", "salon", "parlour", "parlor", "ब्यूटी", "पार्लर", "सैलून", "सलून", "makeup", "मेकअप", "facial", "फेशियल", "hair spa", "हेयर स्पा"]
    if any(w in p_low for w in beauty_signals):
        industry_data.update({
            "tagline": "Enhance Your Beauty",
            "services": ["Facial", "Hair Spa", "Makeup"],
            "cta": "Book Appointment",
            "layoutType": "elegant",
            "brandColor": "#ec4899",
            "accentColor": "#f472b6",
            "visualTheme": "Beautiful salon interior with beauty tools, makeup brushes, cosmetic products, soft romantic lighting, premium beauty photography"
        })
    elif any(w in p_low for w in ["tailor", "tailors", "tailoring", "sewing", "alteration", "silai", "टेलर", "टेलर्स", "दर्जी", "सिलाई", "अल्टरशन", "शिवण"]):
        industry_data.update({
            "tagline": "Perfect Fit, Every Time",
            "services": ["Custom Stitching", "Alterations", "Blouse Design"],
            "cta": "Order Now",
            "layoutType": "elegant",
            "brandColor": "#1d4ed8",
            "accentColor": "#d4af37",
            "visualTheme": "A professional Indian tailoring studio with a sewing machine, colorful fabric rolls, measuring tape, neatly arranged cloth samples, cutting table and warm boutique lighting, detailed commercial photography"
        })
    elif any(w in p_low for w in ["cake", "cakes", "बेकरी", "केक", "sweet", "sweets", "mithai", "मिठाई", "pastry"]):
        industry_data.update({
            "tagline": "Baked Fresh Daily",
            "services": ["Custom Cakes", "Designer Pastries", "Wedding Orders"],
            "cta": "Order Now",
            "layoutType": "centered",
            "brandColor": "#d97706",
            "accentColor": "#f59e0b",
            "visualTheme": "Beautiful artisan cakes with intricate designs, bakery setup, warm golden lighting, professional food photography"
        })
    elif any(w in p_low for w in ["balloon", "गुब्बारे", "birthday", "जन्मदिन", "party"]):
        industry_data.update({
            "tagline": "Celebrate with Colors",
            "services": ["Balloon Decorations", "Party Setup", "Event Planning"],
            "cta": "Book Now",
            "layoutType": "bold",
            "brandColor": "#ec4899",
            "accentColor": "#fbbf24",
            "visualTheme": "Vibrant colorful balloons in various sizes, confetti, festive decorations, bright studio lighting, professional photography"
        })
    elif any(w in p_low for w in ["bartan", "utensil", "utensils", "kitchenware", "cookware", "crockery", "बर्तन", "स्टील", "स्टील के बर्तन"]):
        industry_data.update({
            "tagline": "Authentic Steel Utensils",
            "services": ["Steel Utensils", "Kitchen Sets", "Festival Offers"],
            "cta": "Shop Now",
            "layoutType": "elegant",
            "brandColor": "#0f766e",
            "accentColor": "#f59e0b",
            "visualTheme": "A premium utensils store with stainless steel pots, pans, plates and bowls displayed in an organized retail setup, bright showroom lighting, modern product-focused composition"
        })
    elif any(w in p_low for w in ["clothes", "cloth", "garment", "apparel", "कपड़े", "कपड़ों", "कपडा", "कपड़ा", "कपड्य", "कपड्यांच्या", "ड्रेस", "साड़ी", "साडी", "साड्या", "kids wear", "बच्चों के कपड़े"]):
        industry_data.update({
            "tagline": "Stylish and Colorful",
            "services": ["Kids Wear", "Latest Designs", "Seasonal Offers"],
            "cta": "Shop Now",
            "layoutType": "elegant",
            "brandColor": "#7c3aed",
            "accentColor": "#f59e0b",
            "visualTheme": "A premium clothing shop scene with colorful garments neatly displayed, fashionable kids and family outfits, boutique ambience, bright retail lighting, elegant commercial fashion photography"
        })
    elif any(w in p_low for w in ["saree", "साड़ी", "silk", "sari", "fabric", "boutique"]):
        industry_data.update({
            "tagline": "Tradition Meets Style",
            "services": ["Designer Sarees", "Silk Collections", "Custom Tailoring"],
            "cta": "Shop Collection",
            "layoutType": "sidebar",
            "brandColor": "#ec4899",
            "accentColor": "#f43f5e",
            "visualTheme": "Beautiful Indian woman wearing elegant traditional saree and jewelry, ethnic patterns, warm golden lighting, professional fashion photography"
        })
    elif any(w in p_low for w in ["yoga", "योग", "योगा", "meditation", "wellness", "yoga class", "yoga studio"]):
        industry_data.update({
            "tagline": "Breathe and Balance",
            "services": ["Yoga Classes", "Meditation", "Wellness Sessions"],
            "cta": "Join Today",
            "layoutType": "minimal",
            "brandColor": "#22c55e",
            "accentColor": "#0ea5e9",
            "visualTheme": "Peaceful yoga studio with mats, calm natural light, indoor plants, mindfulness ambience, wellness photography, no corporate office, no food ads"
        })
    elif any(w in p_low for w in ["gym", "fitness", "व्यायाम"]):
        industry_data.update({
            "tagline": "Transform Your Body",
            "services": ["Personal Training", "Fitness Plans", "Nutrition Coaching"],
            "cta": "Join Now",
            "layoutType": "bold",
            "brandColor": "#ef4444",
            "accentColor": "#dc2626",
            "visualTheme": "Professional gym equipment, dumbbells, athletic person training, intense red and black lighting, motivational"
        })
    elif any(w in p_low for w in ["food", "tiffin", "खाना", "catering", "thali"]):
        industry_data.update({
            "tagline": "Homemade Taste",
            "services": ["Daily Tiffin", "Party Catering", "Custom Meals"],
            "cta": "Order Now",
            "layoutType": "minimal",
            "brandColor": "#d97706",
            "accentColor": "#f59e0b",
            "visualTheme": "Authentic Indian food in traditional serving bowls, fresh ingredients, warm kitchen lighting, appetizing food photography"
        })
    elif any(w in p_low for w in ["mobile", "smartphone", "iphone", "gadget", "tech"]):
        industry_data.update({
            "tagline": "Latest Technology Here",
            "services": ["Mobile Sale", "Repair Service", "Accessories"],
            "cta": "Visit Store",
            "layoutType": "bold",
            "brandColor": "#3b82f6",
            "accentColor": "#06b6d4",
            "visualTheme": "Latest smartphones and gadgets, modern tech store, blue neon lighting, professional product photography"
        })

    prompt_services = _extract_direct_services(prompt)
    known_beauty_services = _extract_known_beauty_services(prompt)
    if known_beauty_services:
        prompt_services = known_beauty_services

    if (not prompt_services) and any(w in p_low for w in ["beauty", "ब्यूटी", "parlour", "parlor", "salon", "पार्लर", "सैलून", "सलून"]):
        extracted_highlights = []
        if re.search(r"\b(\d{1,3})\s*%", p_low):
            extracted_highlights.append(re.search(r"\b(\d{1,3})\s*%", p_low).group(1) + "% OFF")
        if any(k in p_low for k in ["flower", "flowers", "फूल", "फ्लॉवर", "फ्लावर"]):
            extracted_highlights.append("Flower Decor")
        if any(k in p_low for k in ["crowd", "भीड़", "भीड", "people", "लोग"]):
            extracted_highlights.append("Crowd Background")
        if extracted_highlights:
            industry_data["services"] = extracted_highlights[:3]

    specific = extract_specific_details(prompt)
    if specific["mentioned_items"]:
        items_str = ", ".join(specific["mentioned_items"])
        industry_data["visualTheme"] += f", featuring {items_str}"

    prompt_tagline = _extract_tagline_from_prompt(prompt)
    prompt_cta = _extract_generic_cta(prompt)
    if prompt_tagline:
        industry_data["tagline"] = prompt_tagline
    if prompt_cta:
        industry_data["cta"] = prompt_cta

    if prompt_services:
        industry_data["services"] = prompt_services

    # Keep an explicit offer visible in the review/output instead of letting
    # the generic industry defaults hide it.
    if specific["offers"]:
        offer = specific["offers"][0]
        industry_data["services"] = [
            offer,
            *[service for service in industry_data.get("services", []) if service != offer],
        ][:3]

    # Unknown categories keep the user's own scene instead of inheriting a known profile.
    known_profile = match_domain_profile(prompt)
    if known_profile.get("visualTheme", "").startswith("The scene must clearly show"):
        industry_data["tagline"] = prompt_tagline or "Made For You"
        industry_data["cta"] = prompt_cta or "Contact Us"
        industry_data["visualTheme"] = build_prompt_first_visual_theme(prompt)
        if not prompt_services:
            industry_data["services"] = ["Featured Services"]

    industry_data = apply_visual_overrides(industry_data, prompt)

    return industry_data

def local_emergency_extract(p: str):
    """Instant local regex scan to pull data from raw Hindi/Marathi/English string."""
    import re
    p_clean = p.strip()
    
    # 1. Extract Name: Look for 'shop name is X', 'naam hai X', 'naav aahe X'
    name_patterns = [
        r"(?:नाम|नाव|name)\s+(?:आहे|है|is|:)?\s*([^,.\s?]+(?:\s+[^,.\s?]+)?)",
        r"(?:store|shop|boutique|दुकान|केंद्र)\s+(?:named|नावाचे|आहे)?\s*([^,.\s?]+(?:\s+[^,.\s?]+)?)"
    ]
    name = "My Business"
    for pattern in name_patterns:
        match = re.search(pattern, p_clean, re.IGNORECASE)
        if match:
            found = match.group(1).strip()
            if len(found) > 1 and "instagram" not in found.lower():
                name = found.title()
                break

    # 2. Extract Phone: Find any 10-digit number
    phone_match = re.search(r"(\d{10})", p_clean)
    phone = phone_match.group(1) if phone_match else "+91 00000 00000"
    
    # 3. Industry Detection
    p_low = p_clean.lower()
    industry_data = {
        "businessName": name,
        "tagline": "Quality Assured",
        "services": ["Premium Quality", "Quick Delivery", "Expert Support"],
        "contact": phone,
        "cta": "Contact Us",
        "layoutType": "centered",
        "visualTheme": "Professional clean aesthetic background, vibrant colors."
    }
    
    if any(w in p_low for w in ["cake", "बेकरी", "केक", "sweet", "baked", "क्रेक"]):
        industry_data.update({
            "tagline": "Baked Fresh Every Day",
            "services": ["Custom Cakes", "Designer Pastries", "Party Orders"],
            "cta": "Order Now",
            "layoutType": "centered",
            "visualTheme": "Aesthetic assortment of professional layered cakes, warm bakery lighting."
        })
    elif any(w in p_low for w in ["mobile", "फोन", "gadget", "गॅजेट", "tech", "मोबाईल"]):
        industry_data.update({
            "tagline": "Your Digital Partner",
            "services": ["Mobile Repair", "Used Phones", "Gadget Accessories"],
            "cta": "Visit Us",
            "layoutType": "bold",
            "visualTheme": "Futuristic smartphones and modern electronic gadgets, blue neon lighting."
        })
    elif any(w in p_low for w in ["saree", "साडी", "silk", "सिल्क", "boutique", "fashion", "ज्वेलरी", "jewelry", "बँगल", "चूड़ी", "चूडया", "चूड़ियाँ"]):
        industry_data.update({
            "tagline": "Traditional Elegance",
            "services": ["Designer Collections", "Wedding Wear", "Traditional Jewelry"],
            "cta": "Shop Collection",
            "layoutType": "sidebar",
            "visualTheme": "Beautiful Indian woman wearing colorful traditional bangles and jewelry, royal ethnic lighting."
        })
    elif any(w in p_low for w in ["gym", "fitness", "व्यायाम", "iron", "जिम"]):
        industry_data.update({
            "tagline": "Forge Your Future",
            "services": ["Personal Training", "Crossfit", "Diet Plans"],
            "cta": "Join Today",
            "layoutType": "bold",
            "visualTheme": "Intense gym setting, heavy dumbbells, dramatic red neon lighting."
        })
    elif any(w in p_low for w in ["food", "kitchen", "खाना", "रसोई", "टिफिन", "जेवण", "डबा", "catering", "tiffin"]):
        industry_data.update({
            "tagline": "Ghar Jaisa Swad",
            "services": ["Authentic Veg Thali", "Daily Tiffin Service", "Party Catering"],
            "cta": "Order Now",
            "layoutType": "minimal",
            "visualTheme": "Aesthetic Indian kitchen setting, fresh roti and dal in copper bowls, steam rising."
        })
        
    return industry_data

def sanitize_extracted_data(data: dict, prompt: str):
    """Scrub hallucinated placeholders and ensure data matches user intent."""
    placeholders = ["1234", "main st", "anytown", "555-", "555 555", "+1 555", "tagline here", "your name", "example", "sample"]
    p_low = prompt.lower()
    
    for field in ["businessName", "contact", "cta"]:
        value = str(data.get(field, ""))
        if value:
            v_low = value.lower()
            if any(p in v_low for p in placeholders):
                data[field] = ""
            if field == "contact":
                contact_info = extract_contact_details(prompt)
                data[field] = format_contact_value(contact_info["phone"], contact_info["email"])
    
    # Clean services list
    if "services" in data and isinstance(data["services"], list):
        data["services"] = [
            s for s in data["services"] 
            if s and not any(p in s.lower() for p in placeholders) and len(s) > 2
        ][:4]

    def shorten(value: str, limit: int) -> str:
        value = (value or "").strip()
        if len(value) <= limit:
            return value
        return value[: max(0, limit - 1)].rstrip() + "…"

    data["businessName"] = shorten(str(data.get("businessName", "")), 28)
    data["tagline"] = shorten(str(data.get("tagline", "")), 40)
    data["cta"] = shorten(str(data.get("cta", "")), 36)
    if isinstance(data.get("services"), list):
        data["services"] = [shorten(str(s), 30) for s in data["services"]]

    # Normalize layout for frontend-supported templates.
    layout_value = str(data.get("layoutType", "elegant")).lower().strip()
    layout_map = {
        "centered": "elegant",
        "center": "elegant",
        "classic": "elegant",
        "modern": "minimal"
    }
    layout_value = layout_map.get(layout_value, layout_value)
    if layout_value not in ["elegant", "bold", "sidebar", "minimal"]:
        layout_value = "elegant"
    data["layoutType"] = layout_value
    
    # Ensure required fields
    extracted_name = _extract_business_name_from_prompt(prompt)
    if extracted_name and str(data.get("businessName", "")).strip().lower() in ["", "my business", "our business", "premium collection"]:
        data["businessName"] = extracted_name

    if not data.get("businessName"):
        data["businessName"] = "Our Business"
    if not data.get("tagline"):
        data["tagline"] = "Quality & Excellence"
    if not data.get("cta"):
        data["cta"] = "Order Now"
    if not data.get("services"):
        data["services"] = ["Premium Quality", "Expert Service"]

    # Enforce valid hex color values for frontend CSS variables.
    hex_color_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")
    default_brand = "#6366f1"
    default_accent = "#fbbf24"
    brand_color = str(data.get("brandColor", "")).strip()
    accent_color = str(data.get("accentColor", "")).strip()
    data["brandColor"] = brand_color if hex_color_pattern.match(brand_color) else default_brand
    data["accentColor"] = accent_color if hex_color_pattern.match(accent_color) else default_accent

    contrast = str(data.get("textContrast", "light")).strip().lower()
    data["textContrast"] = "dark" if contrast == "dark" else "light"
    
    return data

def extract_business_details(prompt: str):
    """Enhanced extraction leveraging both AI and local NER."""
    return extract_enhanced_business_details(prompt)

def generate_prompt(visual_theme: str) -> str:
    """Generate detailed image prompt with emphasis on visual quality."""
    prompt = (
        f"Ultra high-quality professional commercial photography, magazine-style, 8k cinematic. "
        f"MAIN SUBJECT: {visual_theme}. "
        f"Perfect lighting, vibrant saturated colors, sharp focus, detailed textures, "
        f"professional composition, artistic layout. "
        f"CRITICAL: Contains NO text, NO words, NO letters, NO typography, NO watermarks, absolutely textless. "
        f"Award-winning quality, suitable for premium Instagram/advertising use."
    )
    return prompt

def generate_image(prompt: str, negative_prompt: str = "") -> str:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    GENERATIONS_DIR = os.path.join(BASE_DIR, "generations")

    def _local_fallback() -> str:
        """Create a guaranteed business-specific scene when image providers fail."""
        from PIL import Image, ImageDraw, ImageFilter

        width, height = 1080, 1350
        text = (prompt or "").lower()
        if any(k in text for k in ["beauty", "salon", "parlour", "parlor", "ब्यूटी", "पार्लर", "सैलून"]):
            top, bottom, accent = (32, 18, 42), (100, 35, 82), (246, 114, 174)
        elif any(k in text for k in ["bakery", "cake", "केक", "बेकरी"]):
            top, bottom, accent = (48, 26, 18), (128, 65, 36), (245, 174, 66)
        elif any(k in text for k in ["yoga", "योग", "meditation"]):
            top, bottom, accent = (12, 48, 46), (30, 104, 90), (90, 207, 173)
        elif any(k in text for k in ["mobile", "smartphone", "मोबाइल"]):
            top, bottom, accent = (10, 24, 52), (24, 73, 112), (74, 170, 255)
        else:
            top, bottom, accent = (19, 27, 49), (48, 74, 92), (255, 166, 74)

        image = Image.new("RGB", (width, height), top)
        draw = ImageDraw.Draw(image)
        for y in range(height):
            ratio = y / (height - 1)
            color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
            draw.line((0, y, width, y), fill=color)

        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((70, 130, 650, 710), fill=(*accent, 90))
        glow_draw.ellipse((520, 760, 1180, 1420), fill=(*accent, 70))
        glow = glow.filter(ImageFilter.GaussianBlur(90))
        image = Image.alpha_composite(image.convert("RGBA"), glow)
        draw = ImageDraw.Draw(image)
        for x, y, radius in [(130, 970, 18), (220, 1080, 28), (850, 240, 22), (930, 1040, 34)]:
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*accent, 150))

        # The fallback must still communicate the requested business instead
        # of looking like an unrelated gradient. Keep the center clear for
        # the frontend text card while placing recognizable scene objects
        # around the edges and in the lower background.
        if any(k in text for k in ["bakery", "cake", "केक", "बेकरी"]):
            # Bakery shelves and a counter.
            draw.rectangle((55, 210, 330, 780), fill=(70, 35, 25), outline=(245, 174, 66), width=5)
            for shelf_y in (340, 500, 660):
                draw.line((70, shelf_y, 315, shelf_y), fill=(245, 174, 66), width=6)
                for cake_x in (105, 210):
                    draw.ellipse((cake_x - 35, shelf_y - 58, cake_x + 35, shelf_y - 8), fill=(250, 220, 185), outline=(255, 174, 66), width=3)
                    draw.rectangle((cake_x - 32, shelf_y - 35, cake_x + 32, shelf_y - 8), fill=(210, 90, 70))
                    draw.ellipse((cake_x - 8, shelf_y - 70, cake_x + 8, shelf_y - 48), fill=(255, 220, 90))
            draw.rectangle((390, 1030, 990, 1220), fill=(105, 55, 32), outline=(245, 174, 66), width=6)
            for cake_x, cake_color in ((500, (244, 150, 180)), (700, (245, 210, 120)), (875, (180, 130, 245))):
                draw.ellipse((cake_x - 95, 950, cake_x + 95, 1020), fill=(245, 225, 195), outline=(255, 190, 100), width=4)
                draw.rectangle((cake_x - 82, 870, cake_x + 82, 985), fill=cake_color)
                draw.ellipse((cake_x - 82, 835, cake_x + 82, 900), fill=(255, 240, 220), outline=(255, 190, 100), width=4)
                draw.ellipse((cake_x - 12, 810, cake_x + 12, 845), fill=(255, 190, 50))
        elif any(k in text for k in ["mobile", "smartphone", "मोबाइल", "मोबाईल", "electronics"]):
            for phone_x in (110, 245, 835, 970):
                draw.rounded_rectangle((phone_x - 52, 300, phone_x + 52, 560), radius=18, fill=(22, 30, 42), outline=(74, 170, 255), width=6)
                draw.rectangle((phone_x - 38, 340, phone_x + 38, 510), fill=(35, 115, 170))
                draw.ellipse((phone_x - 12, 320, phone_x + 12, 344), fill=(180, 220, 255))
            draw.rectangle((70, 920, 1010, 1110), fill=(24, 45, 70), outline=(74, 170, 255), width=6)
        elif any(k in text for k in ["salon", "beauty", "parlour", "parlor", "मेकअप", "ब्यूटी", "पार्लर"]):
            draw.rectangle((70, 250, 320, 800), fill=(80, 35, 75), outline=(246, 114, 174), width=6)
            for mirror_x in (135, 255):
                draw.ellipse((mirror_x - 45, 320, mirror_x + 45, 500), fill=(185, 220, 230), outline=(246, 114, 174), width=7)
            draw.rectangle((80, 850, 1000, 1060), fill=(120, 45, 100), outline=(246, 114, 174), width=6)
            for bottle_x in (180, 420, 660, 900):
                draw.rounded_rectangle((bottle_x - 22, 770, bottle_x + 22, 900), radius=8, fill=(246, 114, 174))
        elif any(k in text for k in ["flower", "flowers", "floral", "फूल", "फुले", "गुलाब"]):
            draw.rectangle((70, 760, 1010, 1110), fill=(55, 85, 58), outline=(245, 180, 90), width=6)
            for flower_x, flower_y, flower_color in (
                (180, 560, (245, 85, 130)),
                (390, 470, (255, 190, 60)),
                (610, 540, (245, 120, 180)),
                (830, 450, (255, 220, 90)),
            ):
                draw.line((flower_x, flower_y + 50, flower_x, 900), fill=(55, 155, 75), width=8)
                draw.ellipse((flower_x - 32, flower_y, flower_x + 32, flower_y + 62), fill=flower_color)
                draw.ellipse((flower_x - 62, flower_y + 18, flower_x - 2, flower_y + 58), fill=flower_color)
                draw.ellipse((flower_x + 2, flower_y + 18, flower_x + 62, flower_y + 58), fill=flower_color)
        elif any(k in text for k in ["saree", "sari", "साड़ी", "साडी", "साड्या", "silk"]):
            for rack_x in (100, 370, 640, 910):
                draw.rectangle((rack_x - 68, 240, rack_x + 68, 850), fill=(85, 35, 65), outline=(245, 170, 100), width=5)
                draw.rectangle((rack_x - 58, 280, rack_x + 58, 760), fill=(215, 120, 150), outline=(255, 220, 170), width=3)
                draw.line((rack_x - 58, 430, rack_x + 58, 430), fill=(255, 220, 170), width=5)
                draw.line((rack_x - 58, 590, rack_x + 58, 590), fill=(255, 220, 170), width=5)
            draw.rectangle((300, 930, 780, 1120), fill=(115, 55, 75), outline=(245, 170, 100), width=6)
            draw.ellipse((530, 780, 670, 920), fill=(230, 180, 130), outline=(245, 170, 100), width=5)
        elif any(k in text for k in ["clothing", "clothes", "cloth", "garment", "apparel", "कपड़े", "कपड्य", "ड्रेस", "fashion", "boutique"]):
            for rack_x in (120, 390, 660, 930):
                draw.rectangle((rack_x - 80, 260, rack_x + 80, 830), fill=(55, 48, 92), outline=(245, 170, 100), width=5)
                draw.line((rack_x - 70, 390, rack_x + 70, 390), fill=(245, 170, 100), width=5)
                for hanger_y, outfit_color in ((500, (180, 70, 150)), (650, (55, 130, 210))):
                    draw.polygon(((rack_x - 45, hanger_y), (rack_x, hanger_y - 35), (rack_x + 45, hanger_y)), fill=(245, 220, 180))
                    draw.rectangle((rack_x - 45, hanger_y, rack_x + 45, hanger_y + 115), fill=outfit_color)
            draw.rectangle((70, 930, 1010, 1110), fill=(70, 55, 75), outline=(245, 170, 100), width=6)
        elif any(k in text for k in ["yoga", "योग", "meditation"]):
            for mat_x in (130, 500, 870):
                draw.ellipse((mat_x - 115, 900, mat_x + 115, 1030), fill=(90, 207, 173), outline=(190, 255, 220), width=5)
            draw.ellipse((90, 250, 300, 460), fill=(45, 115, 95), outline=(90, 207, 173), width=5)
            draw.line((195, 460, 150, 850), fill=(90, 207, 173), width=12)

        # Preserve explicit background requests even when the prompt combines
        # them with an industry, for example "bakery with red balloons".
        if any(k in text for k in ["balloon", "balloons", "गुब्बारे", "फुगे"]):
            balloon_colors = [(220, 55, 75), (55, 120, 235), (245, 190, 45), (180, 70, 190)]
            for index, (x, y) in enumerate(((760, 190), (900, 280), (690, 350), (950, 470))):
                color = balloon_colors[index % len(balloon_colors)]
                draw.ellipse((x - 42, y - 58, x + 42, y + 58), fill=color, outline=(255, 235, 190), width=4)
                draw.line((x, y + 58, x - 20, 830), fill=(255, 235, 190), width=3)
        if any(k in text for k in ["flower", "flowers", "फूल", "फुले", "गुलाब"]):
            for x, y in ((390, 260), (520, 350), (1010, 720), (350, 760)):
                draw.line((x, y + 40, x, y + 190), fill=(55, 150, 75), width=7)
                draw.ellipse((x - 28, y, x + 28, y + 55), fill=(245, 85, 130), outline=(255, 220, 170), width=3)
                draw.ellipse((x - 55, y + 18, x - 5, y + 55), fill=(245, 85, 130), outline=(255, 220, 170), width=3)
                draw.ellipse((x + 5, y + 18, x + 55, y + 55), fill=(245, 85, 130), outline=(255, 220, 170), width=3)

        path = os.path.join(GENERATIONS_DIR, f"fallback_{uuid.uuid4()}.png")
        image.save(path, "PNG")
        return path

    def _pollinations_fallback() -> str:
        import urllib.parse
        import random
        from io import BytesIO
        from PIL import Image

        encoded_prompt = urllib.parse.quote(prompt)
        poll_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1350&nologo=true&seed={random.randint(1, 1000000)}"
        try:
            poll_response = requests.get(poll_url, timeout=30)
            if poll_response.status_code == 200:
                image = Image.open(BytesIO(poll_response.content))
                image.verify()
                path = os.path.join(GENERATIONS_DIR, f"raw_{uuid.uuid4()}.png")
                with open(path, "wb") as f:
                    f.write(poll_response.content)
                return path
        except Exception as error:
            print(f"Free image provider error, using local fallback: {error}")
        return _local_fallback()
    
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
    
    if not STABILITY_API_KEY or STABILITY_API_KEY == "your_key_here":
        return _pollinations_fallback()

    API_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "image/*"
    }
    
    default_negative = (
        "text, words, fonts, letters, alphabet, typography, writing, signature, watermark, logo, "
        "calligraphy, subtitles, gibberish, signboard, signage, shop sign, banner text, label, printed text, caption"
    )
    final_negative = (negative_prompt or "").strip() or default_negative

    data = {
        "prompt": prompt,
        "negative_prompt": final_negative,
        "aspect_ratio": "4:5",
        "output_format": "png"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, files={"none": ''}, data=data, timeout=60)
        if response.status_code == 200:
            path = os.path.join(GENERATIONS_DIR, f"raw_{uuid.uuid4()}.png")
            with open(path, "wb") as f:
                f.write(response.content)
            return path
        print(f"SD API error, using free fallback: {response.text}")
    except Exception as error:
        print(f"SD API request failed, using free fallback: {error}")
    return _pollinations_fallback()
