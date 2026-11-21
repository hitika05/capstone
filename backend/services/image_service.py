from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
import uuid
import numpy as np
import re

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "NotoSansDevanagari-Regular.ttf")

def get_font(size, text=""):
    """Get appropriate font with fallback support."""
    try:
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
        if not has_devanagari:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except:
                pass
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def detect_image_brightness(image: Image.Image) -> float:
    """Detect overall brightness to determine text color."""
    img_array = np.array(image.convert('L'))
    return np.mean(img_array) / 255.0

def calculate_text_color(image_brightness: float) -> tuple:
    """Calculate optimal text color based on background brightness."""
    if image_brightness < 0.5:
        # Dark background - use white text
        return (255, 255, 255, 255), (0, 0, 0, 200)  # text, shadow
    else:
        # Light background - use dark text
        return (0, 0, 0, 255), (255, 255, 255, 150)  # text, shadow

def apply_enhanced_text_overlay(
    image_path: str, 
    business_name: str, 
    tagline: str, 
    contact: str = "",
    services: list = None,
    overlay_lang: str = "English"
) -> str:
    """Apply enhanced text overlay with professional styling and visibility."""
    from deep_translator import GoogleTranslator
    
    if services is None:
        services = []
    
    # Translate if needed
    if overlay_lang == "Hindi" or overlay_lang == "Marathi":
        try:
            target = 'hi' if overlay_lang == "Hindi" else 'mr'
            business_name = GoogleTranslator(source='en', target=target).translate(business_name)
            if tagline:
                tagline = GoogleTranslator(source='en', target=target).translate(tagline)
            contact = GoogleTranslator(source='en', target=target).translate(contact) if contact else ""
        except Exception as e:
            print(f"Translation error: {e}")
    
    # Open image and enhance it for better text visibility
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    
    # Pillow autocontrast does not support RGBA directly, so process RGB and restore alpha.
    alpha = img.getchannel("A")
    rgb = img.convert("RGB")
    rgb_enhanced = ImageOps.autocontrast(rgb, cutoff=5)
    img_enhanced = rgb_enhanced.convert("RGBA")
    img_enhanced.putalpha(alpha)
    
    # Detect brightness and get optimal colors
    brightness = detect_image_brightness(Image.open(image_path).convert('L'))
    text_color, shadow_color = calculate_text_color(brightness)
    
    # Create drawing context
    draw = ImageDraw.Draw(img_enhanced)
    
    # Calculate font sizes based on dimensions and text length
    base_title_size = max(
        int(height * 0.08),
        int(width / (len(business_name.split()) * 8))
    )
    base_tagline_size = max(int(height * 0.04), int(height * 0.035))
    
    title_font = get_font(base_title_size, business_name)
    tagline_font = get_font(base_tagline_size, tagline)
    contact_font = get_font(int(height * 0.03), contact)
    
    # Calculate word wrapping for long titles
    def wrap_text(text, font, max_width, draw_obj):
        """Wrap text to fit width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw_obj.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    # Wrap title if needed
    title_lines = wrap_text(business_name, title_font, int(width * 0.85), draw)
    
    # Draw text with advanced shadow effect
    def draw_text_advanced(text, font, y_pos, draw_obj, bg_color, color, stroke_width=5):
        """Draw text with enhanced shadow and stroke."""
        if not text:
            return y_pos
        
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        
        # Draw shadow with enhanced visibility
        shadow_offset = stroke_width // 2
        draw_obj.text(
            (x + shadow_offset, y_pos + shadow_offset),
            text, font=font, fill=bg_color, stroke_width=stroke_width, stroke_fill=bg_color
        )
        
        # Draw main text with stroke
        draw_obj.text(
            (x, y_pos),
            text, font=font, fill=color, stroke_width=max(2, stroke_width - 2), stroke_fill=shadow_color
        )
        
        return y_pos + (bbox[3] - bbox[1]) + int(height * 0.02)
    
    # Draw business name (multi-line if needed)
    current_y = int(height * 0.08)
    for line in title_lines:
        current_y = draw_text_advanced(
            line, title_font, current_y, draw,
            shadow_color, text_color, stroke_width=6
        )
    
    # Draw tagline
    if tagline:
        current_y = draw_text_advanced(
            tagline, tagline_font, int(height * 0.72), draw,
            shadow_color, text_color, stroke_width=4
        )
    
    # Draw contact at bottom
    if contact:
        draw_text_advanced(
            f"📞 {contact}", contact_font, int(height * 0.92), draw,
            shadow_color, text_color, stroke_width=3
        )
    
    # Save enhanced image
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    GENERATIONS_DIR = os.path.join(BASE_DIR, "generations")
    final_path = os.path.join(GENERATIONS_DIR, f"final_{uuid.uuid4()}.png")
    img_enhanced.save(final_path, "PNG")
    return final_path

def apply_devanagari_overlay(image_path: str, business_name: str, tagline: str, overlay_lang: str = "English") -> str:
    """Legacy function for backward compatibility."""
    return apply_enhanced_text_overlay(image_path, business_name, tagline, "", [], overlay_lang)

def generate_pricing_image(items_text: str, business_name: str, overlay_lang: str = "English") -> str:
    raw_text = (items_text or "").strip()

    # Drop spoken intro before the actual list when user says phrases like "price list ...".
    intro_markers = [
        "price list", "price-list", "rate list", "menu", "mrp",
        "प्राइस लिस्ट", "रेट लिस्ट", "मूल्य सूची", "दर सूची", "मेन्यू"
    ]
    scan_lower = raw_text.lower()
    for marker in intro_markers:
        idx = scan_lower.find(marker)
        if idx != -1:
            before_marker = raw_text[:idx].strip(" :,-।")
            after_marker = raw_text[idx + len(marker):].strip(" :,-।")
            # In natural speech the list can come before the words
            # "price list", e.g. "... pastry 80 की हिंदी प्राइस लिस्ट".
            # Preserve that content instead of replacing it with "बनाएं".
            if re.search(r"\d|₹|rs\.?|रुपये", before_marker, re.IGNORECASE):
                raw_text = re.sub(
                    r"\s+(?:की|का|के|ची|चा|चे)\s+(?:हिंदी|मराठी|english|इंग्लिश|मराठी)?\s*$",
                    "",
                    before_marker,
                    flags=re.IGNORECASE,
                ).strip()
            else:
                raw_text = after_marker
            scan_lower = raw_text.lower()
            break

    # If upstream extraction returned a generic fallback, infer name from spoken prefix.
    fallback_names = {"my business", "price list", "business", "shop"}
    if (business_name or "").strip().lower() in fallback_names:
        prefix = (items_text or "").strip()
        prefix_low = prefix.lower()
        cut_idx = -1
        for marker in intro_markers:
            i = prefix_low.find(marker)
            if i != -1:
                cut_idx = i
                break
        if cut_idx > 0:
            inferred = prefix[:cut_idx].strip(" :,-।")
            inferred = re.sub(r"\s+", " ", inferred)
            if inferred:
                business_name = inferred

    # Do not let the extracted business name become the first menu item.
    if business_name and raw_text.lower().startswith(business_name.lower()):
        raw_text = raw_text[len(business_name):].strip(" :,-।")
    elif business_name:
        # Remove spoken introductions such as "my shop name is ...".
        name_match = re.search(re.escape(business_name), raw_text, re.IGNORECASE)
        if name_match:
            raw_text = raw_text[name_match.end():]
            raw_text = re.sub(
                r"^\s*(?:है|आहे|is|हैं|आहेत)\s*[,।:;\-]?\s*",
                "",
                raw_text,
                flags=re.IGNORECASE,
            )

    # Convert spoken Hindi/Marathi prices before pairing item names with them.
    number_words = {
        "hi": {
            "शून्य": 0, "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5,
            "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10, "ग्यारह": 11,
            "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16,
            "सत्रह": 17, "अठारह": 18, "उन्नीस": 19, "बीस": 20, "पच्चीस": 25,
            "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60, "सत्तर": 70,
            "अस्सी": 80, "नब्बे": 90, "सौ": 100, "एक सौ": 100, "पांच सौ": 500,
        },
        "mr": {
            "शून्य": 0, "एक": 1, "दोन": 2, "तीन": 3, "चार": 4, "पाच": 5,
            "सहा": 6, "सात": 7, "आठ": 8, "नऊ": 9, "दहा": 10, "अकरा": 11,
            "बारा": 12, "तेरा": 13, "चौदा": 14, "पंधरा": 15, "सोळा": 16,
            "सतरा": 17, "अठरा": 18, "एकोणीस": 19, "वीस": 20, "पंचवीस": 25,
            "तीस": 30, "चाळीस": 40, "पन्नास": 50, "साठ": 60, "सत्तर": 70,
            "ऐंशी": 80, "नव्वद": 90, "शंभर": 100, "पाचशे": 500, "पाचशे रुपये": 500,
        },
    }
    word_map = {**number_words["hi"], **number_words["mr"]}
    for word, value in sorted(word_map.items(), key=lambda pair: len(pair[0]), reverse=True):
        raw_text = re.sub(rf"(?<![\w\u0900-\u097f]){re.escape(word)}(?![\w\u0900-\u097f])", str(value), raw_text, flags=re.IGNORECASE)

    # Parse repeated "item name + price" pairs even when commas are missing.
    pair_pattern = re.compile(
        r"([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s&/\-]{1,50}?)\s*(?:₹|rs\.?|inr|रु\.?|रुपये|रुपये में|रुपयाला)?\s*(\d{1,5})(?=\s*(?:,|$|[A-Za-z\u0900-\u097F]))",
        re.IGNORECASE,
    )

    items = []
    for match in pair_pattern.finditer(raw_text):
        name = re.sub(r"\s+", " ", match.group(1)).strip(" ,.-:;|।")
        name = re.sub(
            r"^(?:और|तथा|एवं|आणि|व|and)\s+",
            "",
            name,
            flags=re.IGNORECASE,
        ).strip()
        price = match.group(2)
        if name and price:
            items.append((name, price))

    # Fallback for unusual formats: split by commas and read last token as price.
    if not items:
        parts = [p.strip() for p in raw_text.split(",") if p.strip()]
        for part in parts:
            m = re.search(r"(\d{1,5})\s*$", part)
            if m:
                price = m.group(1)
                name = part[:m.start()].strip(" ,.-:;|।")
                if name:
                    items.append((name, price))

    if not items:
        items = [(raw_text or "Price List", "")]
            
    width, height = 1080, 1080

    # Pick a tasteful palette by domain hints in spoken text.
    t_low = raw_text.lower()
    if any(k in t_low for k in ["cake", "केक", "pastry", "bakery", "बेकरी"]):
        top_color, bottom_color = (36, 28, 46), (86, 58, 46)
        accent = (245, 174, 66)
    elif any(k in t_low for k in ["beauty", "parlour", "parlor", "salon", "ब्यूटी", "पार्लर", "सैलून", "सलून"]):
        top_color, bottom_color = (33, 25, 56), (73, 36, 84)
        accent = (246, 114, 174)
    else:
        top_color, bottom_color = (19, 34, 56), (24, 74, 96)
        accent = (90, 207, 173)

    # Create smooth vertical gradient background.
    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        mix = y / max(1, height - 1)
        r = int(top_color[0] * (1 - mix) + bottom_color[0] * mix)
        g = int(top_color[1] * (1 - mix) + bottom_color[1] * mix)
        b = int(top_color[2] * (1 - mix) + bottom_color[2] * mix)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Decorative soft glow circles.
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((60, 70, 360, 370), fill=(accent[0], accent[1], accent[2], 70))
    gdraw.ellipse((760, 780, 1060, 1080), fill=(accent[0], accent[1], accent[2], 55))
    glow = glow.filter(ImageFilter.GaussianBlur(45))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Prefer a real generated commercial photograph for the backdrop. The
    # price card remains deterministic so multilingual text stays accurate.
    background_path = ""
    try:
        from services.ai_service import generate_image
        if any(k in t_low for k in ["cake", "केक", "pastry", "bakery", "बेकरी"]):
            scene = "professional bakery counter with realistic decorated cakes and pastries, warm editorial food photography"
        elif any(k in t_low for k in ["salon", "beauty", "पार्लर", "सैलून"]):
            scene = "premium beauty salon interior with realistic mirrors, styling chairs and cosmetics, editorial commercial photography"
        elif any(k in t_low for k in ["jewelry", "jewellery", "bangle", "bracelet", "चूड़ी", "बांगडी"]):
            scene = "luxury jewelry boutique with realistic bangles and jewelry displayed in glass cases, high-end product photography"
        elif any(k in t_low for k in ["menu", "food", "pizza", "restaurant", "रेस्टोरेंट", "खाना", "जेवण", "नाश्ता"]):
            scene = "professional restaurant table with realistic plated food, premium menu photography"
        else:
            scene = "premium retail store interior related to the products in this price list, realistic commercial photography"
        background_path = generate_image(
            f"{scene}, no text, no logos, no illustrations, no icons, no cartoon graphics",
            negative_prompt="cartoon, vector art, clipart, icons, flat illustration, text, logo",
        )
    except Exception as error:
        print(f"Price-list photo background unavailable: {error}")

    if background_path and os.path.exists(background_path) and "fallback_" not in os.path.basename(background_path):
        try:
            photo = Image.open(background_path).convert("RGBA")
            photo = ImageOps.fit(photo, (width, height), method=Image.Resampling.LANCZOS)
            photo = photo.filter(ImageFilter.GaussianBlur(1.2))
            shade = Image.new("RGBA", (width, height), (8, 12, 24, 105))
            img = Image.alpha_composite(photo, shade)
            draw = ImageDraw.Draw(img)
        except Exception as error:
            print(f"Price-list photo background could not be opened: {error}")

    has_devanagari = any('\u0900' <= c <= '\u097F' for c in (business_name + raw_text))
    title_suffix = {
        "Hindi": "प्राइस लिस्ट",
        "Marathi": "किंमत यादी",
    }.get(overlay_lang, "Price List")

    business_font = get_font(62, business_name)
    suffix_font = get_font(62, title_suffix)
    item_font = get_font(38, "".join(name for name, _ in items))
    price_font = get_font(40, "")

    # Card geometry is content-aware so short lists do not produce large empty areas.
    card_x1, card_y1 = 70, 130
    card_x2 = width - 70

    # Header inside card.
    business_bbox = draw.textbbox((0, 0), business_name, font=business_font)
    dash_bbox = draw.textbbox((0, 0), " - ", font=suffix_font)
    suffix_bbox = draw.textbbox((0, 0), title_suffix, font=suffix_font)
    total_title_width = (business_bbox[2] - business_bbox[0]) + (dash_bbox[2] - dash_bbox[0]) + (suffix_bbox[2] - suffix_bbox[0])
    hx = (width - total_title_width) // 2
    hy = card_y1 + 42

    sub = {
        "Hindi": "बोली गई मूल्य सूची",
        "Marathi": "बोललेली किंमत यादी",
    }.get(overlay_lang, "Spoken Price Sheet")
    subtitle_font = get_font(28, sub)
    sb = draw.textbbox((0, 0), sub, font=subtitle_font)
    sw = sb[2] - sb[0]
    sx = (width - sw) // 2

    # Table layout.
    row_top = hy + 140
    row_height = 62
    left_pad = card_x1 + 34
    right_pad = card_x2 - 34

    max_rows = min(len(items), 12)
    rows_bottom = row_top + max_rows * row_height
    min_card_bottom = hy + 230
    desired_card_bottom = rows_bottom + 48
    card_y2 = min(height - 90, max(min_card_bottom, desired_card_bottom))

    # Layered translucent card, branded header band, and shadow give the
    # price list the same visual weight as the poster designs.
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (card_x1 + 12, card_y1 + 16, card_x2 + 12, card_y2 + 16),
        radius=34, fill=(0, 0, 0, 110)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    img = Image.alpha_composite(img, shadow)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (card_x1, card_y1, card_x2, card_y2),
        radius=34,
        fill=(248, 250, 255, 236),
        outline=(*accent, 230),
        width=4,
    )
    header_bottom = hy + 125
    draw.rounded_rectangle(
        (card_x1 + 4, card_y1 + 4, card_x2 - 4, header_bottom),
        radius=28,
        fill=(*top_color, 245),
    )
    draw.rectangle((card_x1 + 4, header_bottom - 28, card_x2 - 4, header_bottom), fill=(*top_color, 245))
    draw.line((card_x1 + 45, header_bottom, card_x2 - 45, header_bottom), fill=(*accent, 220), width=4)

    title_color = (255, 255, 255, 255)
    draw.text((hx, hy), business_name, font=business_font, fill=title_color, stroke_width=1, stroke_fill=(*accent, 180))
    dash_x = hx + (business_bbox[2] - business_bbox[0])
    draw.text((dash_x, hy), " - ", font=suffix_font, fill=(*accent, 255))
    suffix_x = dash_x + (dash_bbox[2] - dash_bbox[0])
    draw.text((suffix_x, hy), title_suffix, font=suffix_font, fill=title_color)
    draw.text((sx, hy + 74), sub, font=subtitle_font, fill=(235, 240, 255, 255))

    for idx, (name, price) in enumerate(items[:12]):
        y1 = row_top + idx * row_height
        y2 = y1 + row_height - 8
        if y2 > card_y2 - 28:
            break

        # Pillow's ImageDraw writes RGBA values directly; translucent fills
        # therefore become transparent rows instead of blending with the
        # opaque card and make dark text disappear against the background.
        row_bg = (238, 248, 246, 255) if idx % 2 == 0 else (225, 231, 242, 255)
        draw.rounded_rectangle((left_pad - 10, y1, right_pad + 10, y2), radius=12, fill=row_bg)

        name_text = re.sub(r"\s+", " ", name).strip()
        if len(name_text) > 26:
            name_text = name_text[:25].rstrip() + "…"
        row_text = f"{idx + 1}. {name_text}"
        draw.ellipse((left_pad - 2, y1 + 17, left_pad + 10, y1 + 29), fill=(*accent, 230))
        draw.text((left_pad + 18, y1 + 10), row_text, font=item_font, fill=(22, 28, 38, 255))

        if price:
            price_text = f"₹{price}"
            pb = draw.textbbox((0, 0), price_text, font=price_font)
            pw = pb[2] - pb[0]
            draw.text((right_pad - pw - 4, y1 + 9), price_text, font=price_font, fill=(*top_color, 255))
        
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    GENERATIONS_DIR = os.path.join(BASE_DIR, "generations")
    final_path = os.path.join(GENERATIONS_DIR, f"price_{uuid.uuid4()}.png")
    img.save(final_path, "PNG")
    return final_path
