from __future__ import annotations

import csv
import json
import random
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SEED = 0

BUSINESSES = [
    ("bakery", "बेकरी", "बेकरी"),
    ("tailor shop", "दर्जी की दुकान", "शिंपी दुकान"),
    ("beauty salon", "ब्यूटी पार्लर", "ब्युटी सलून"),
    ("mobile shop", "मोबाइल दुकान", "मोबाईल दुकान"),
    ("saree shop", "साड़ी की दुकान", "साडी दुकान"),
    ("grocery", "किराना दुकान", "किराणा दुकान"),
    ("chai stall", "चाय की दुकान", "चहाची टपरी"),
    ("sweet shop", "मिठाई की दुकान", "मिठाई दुकान"),
    ("jewelry", "ज्वेलरी दुकान", "ज्वेलरी दुकान"),
    ("electronics", "इलेक्ट्रॉनिक्स दुकान", "इलेक्ट्रॉनिक्स दुकान"),
    ("flower shop", "फूलों की दुकान", "फुलांचे दुकान"),
    ("yoga studio", "योग स्टूडियो", "योग स्टुडिओ"),
]
COLORS = [
    ("red", "लाल", "लाल"), ("blue", "नीला", "निळा"), ("green", "हरा", "हिरवा"),
    ("pink", "गुलाबी", "गुलाबी"), ("gold", "सुनहरा", "सोनेरी"), ("white", "सफेद", "पांढरा"),
    ("purple", "बैंगनी", "जांभळा"), ("orange", "नारंगी", "नारंगी"),
]
OCCASIONS = [("opening", "उद्घाटन", "उद्घाटन"), ("discount", "छूट", "सवलत"), ("festival", "त्योहार", "सण"), ("service", "सेवा", "सेवा")]
SERVICES = {
    "bakery": [("cakes", "केक", "केक"), ("pastries", "पेस्ट्री", "पेस्ट्री"), ("bread", "ब्रेड", "ब्रेड"), ("cookies", "कुकीज़", "कुकीज")],
    "tailor shop": [("stitching", "सिलाई", "शिवण"), ("alterations", "अल्टरेशन", "अल्टरेशन"), ("blouses", "ब्लाउज", "ब्लाउज"), ("dresses", "ड्रेस", "ड्रेस")],
    "beauty salon": [("makeup", "मेकअप", "मेकअप"), ("hair spa", "हेयर स्पा", "हेअर स्पा"), ("facials", "फेशियल", "फेशियल"), ("nails", "नेल आर्ट", "नेल आर्ट")],
    "mobile shop": [("repairs", "रिपेयर", "रिपेअर"), ("accessories", "एक्सेसरीज़", "अॅक्सेसरीज"), ("phones", "फोन", "फोन"), ("chargers", "चार्जर", "चार्जर")],
    "saree shop": [("sarees", "साड़ियां", "साड्या"), ("lehengas", "लहंगे", "लेहेंगा"), ("blouses", "ब्लाउज", "ब्लाउज"), ("bridal wear", "ब्राइडल वियर", "ब्राइडल वियर")],
    "grocery": [("grains", "अनाज", "धान्य"), ("spices", "मसाले", "मसाले"), ("fruits", "फल", "फळे"), ("vegetables", "सब्ज़ियां", "भाज्या")],
    "chai stall": [("tea", "चाय", "चहा"), ("coffee", "कॉफी", "कॉफी"), ("snacks", "नाश्ता", "नाश्ता"), ("samosa", "समोसा", "समोसा")],
    "sweet shop": [("laddoo", "लड्डू", "लाडू"), ("jalebi", "जलेबी", "जिलेबी"), ("barfi", "बर्फी", "बर्फी"), ("cakes", "केक", "केक")],
    "jewelry": [("bangles", "चूड़ियां", "बांगड्या"), ("necklaces", "हार", "हार"), ("rings", "अंगूठियां", "अंगठ्या"), ("earrings", "झुमके", "कानातले")],
    "electronics": [("laptops", "लैपटॉप", "लॅपटॉप"), ("printers", "प्रिंटर", "प्रिंटर"), ("earbuds", "ईयरबड्स", "इअरबड्स"), ("repairs", "रिपेयर", "दुरुस्ती")],
    "flower shop": [("roses", "गुलाब", "गुलाब"), ("bouquets", "गुलदस्ते", "गुच्छ"), ("wedding flowers", "शादी के फूल", "लग्नाची फुले"), ("decor", "सजावट", "सजावट")],
    "yoga studio": [("yoga", "योग", "योग"), ("meditation", "ध्यान", "ध्यान"), ("breathing", "प्राणायाम", "प्राणायाम"), ("wellness", "वेलनेस", "वेलनेस")],
}


def fields(row):
    return ["design_type", "business_type", "colors", "occasion", "shop_name", "services", "offer_percent", "contact"]


def build_command(idx: int, language: str, style: int, rng: random.Random, variant: int = 0) -> dict:
    business = BUSINESSES[idx % len(BUSINESSES)]
    color = COLORS[(idx + style) % len(COLORS)]
    occasion = OCCASIONS[(idx + style) % len(OCCASIONS)]
    service_values = SERVICES[business[0]]
    selected = [service_values[(idx + j) % len(service_values)] for j in range(2 + (idx + style) % 3)]
    shop_name = f"{['सूर्य','श्री','नव','आनंद','किरण','मधुर'][idx % 6]} {['स्टाइल','कला','सेवा','कॉर्नर','हाउस'][style % 5]}"
    offer = 10 + ((idx * 7 + style * 3 + variant) % 31)
    contact = f"98{(idx * 7919 + style * 103 + variant) % 100000000:08d}"
    use_color = (idx + style) % 10 >= 3
    lang_i = 1 if language == "hi" else 2
    lang = "Hindi" if language == "hi" else "Marathi"
    business_name = business[lang_i]
    color_name = color[lang_i]
    occasion_name = occasion[lang_i]
    service_names = [item[lang_i] for item in selected]
    styles = {
        1: f"मेरी {business_name} का नाम {shop_name} है, {', '.join(service_names)} मिलते हैं, {occasion_name} के लिए इंस्टाग्राम पोस्ट बनाओ, {offer} प्रतिशत ऑफर और संपर्क {contact} है" if language == "hi" else f"माझ्या {business_name}चे नाव {shop_name} आहे, {', '.join(service_names)} मिळतात, {occasion_name}साठी इंस्टाग्राम पोस्ट करा, {offer} टक्के ऑफर आणि संपर्क {contact} आहे",
        2: f"भाई {shop_name} {business_name} है, services हैं {', '.join(service_names)}, थोड़ा premium पोस्ट चाहिए, {occasion_name}, offer {offer}% और phone {contact}" if language == "hi" else f"अहो {shop_name} {business_name} आहे, services आहेत {', '.join(service_names)}, थोडी premium पोस्ट हवी, {occasion_name}, offer {offer}% आणि phone {contact}",
        3: f"{shop_name} के लिए एक clean insta design चाहिए; {business_name}, {', '.join(service_names)}, {occasion_name}, call {contact}, {offer}% discount" if language == "hi" else f"{shop_name}साठी clean insta design पाहिजे; {business_name}, {', '.join(service_names)}, {occasion_name}, call {contact}, {offer}% discount",
        4: f"एक काम करो, {shop_name} {business_name} का banner बना दो, {', '.join(service_names)} और {occasion_name} वाला mood, WhatsApp {contact}, {offer}% बचत" if language == "hi" else f"एक काम करा, {shop_name} {business_name}चा banner करा, {', '.join(service_names)} आणि {occasion_name}चा mood, WhatsApp {contact}, {offer}% बचत",
    }
    command = styles[style]
    if use_color:
        command += f", {color_name} रंग" if language == "hi" else f", {color_name} रंग"
    english = f"Create an Instagram design for {business[0]} named {shop_name}, featuring {', '.join(x[0] for x in selected)}, for {occasion[0]}, with a {color[0]} palette, a {offer}% offer, and contact {contact}."
    gold = {
        "design_type": "banner" if style == 4 else "instagram_post",
        "business_type": business[0],
        "colors": [color[0]] if use_color else [],
        "occasion": occasion[0],
        "shop_name": shop_name,
        "services": [x[0] for x in selected],
        "offer_percent": offer,
        "contact": contact,
    }
    return {"id": idx + 1, "command": command, "language": language, "style": style, "split": "dev" if style <= 2 else "test", "english_reference": english, **gold}


def write_csv(path: Path, rows: list[dict], columns: list[str]):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns); writer.writeheader(); writer.writerows(rows)


def main(seed: int = SEED, data_dir: Path = DATA):
    rng = random.Random(seed); data_dir.mkdir(parents=True, exist_ok=True)
    rows = [build_command(i, language, style, rng) for language in ("hi", "mr") for i in range(60) for style in [1 + (i % 4)]][:120]
    # The construction above interleaves languages deterministically; force exactly 60 per language.
    rows = [build_command(i, "hi", 1 + (i % 4), rng, seed) for i in range(60)] + [build_command(i + 60, "mr", 1 + (i % 4), rng, seed) for i in range(60)]
    command_cols = ["id", "command", "language", "style", "split", "english_reference", "design_type", "business_type", "colors", "occasion", "shop_name", "services", "offer_percent", "contact"]
    for row in rows:
        for key in ["colors", "services"]:
            row[key] = json.dumps(row[key], ensure_ascii=False)
    write_csv(data_dir / "commands.csv", rows, command_cols)
    price_rows = []
    products = [("tea", "चाय", "चहा"), ("coffee", "कॉफी", "कॉफी"), ("cake", "केक", "केक"), ("saree", "साड़ी", "साडी"), ("facial", "फेशियल", "फेशियल"), ("charger", "चार्जर", "चार्जर")]
    for idx in range(60):
        lang = "hi" if idx % 2 == 0 else "mr"; li = 1 if lang == "hi" else 2; style = idx % 3 + 1
        selected = [products[(idx + j) % len(products)] for j in range(3)]
        pairs = [(p[0], 20 + ((idx + j) * 37 + seed) % 480) for j, p in enumerate(selected)]
        if style == 1: text = ", ".join(f"{p[li]} {price}" for p, (_, price) in zip(selected, pairs))
        elif style == 2: text = ", ".join(f"{price} रुपये {p[li]}" for p, (_, price) in zip(selected, pairs)) if lang == "hi" else ", ".join(f"{price} रुपये {p[li]}" for p, (_, price) in zip(selected, pairs))
        else: text = ", ".join(f"{p[li]} {['बीस','पचास','सौ'][j]}" if lang == "hi" else f"{p[li]} {['वीस','पन्नास','शंभर'][j]}" for j, p in enumerate(selected))
        price_rows.append({"id": idx + 1, "language": lang, "style": style, "text": text, "gold_pairs": json.dumps(pairs, ensure_ascii=False)})
    write_csv(data_dir / "price_lists.csv", price_rows, ["id", "language", "style", "text", "gold_pairs"])
    taxonomy = {"design_type": ["instagram_post", "banner"], "business_type": [b[0] for b in BUSINESSES], "colors": {"english": [c[0] for c in COLORS], "hindi": [c[1] for c in COLORS], "marathi": [c[2] for c in COLORS]}, "occasion": [o[0] for o in OCCASIONS]}
    (data_dir / "taxonomy.json").write_text(json.dumps(taxonomy, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"seed": seed, "commands": len(rows), "hindi": sum(r["language"] == "hi" for r in rows), "marathi": sum(r["language"] == "mr" for r in rows), "dev": sum(r["split"] == "dev" for r in rows), "test": sum(r["split"] == "test" for r in rows), "price_lists": len(price_rows)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output", type=Path, default=DATA)
    args = parser.parse_args()
    main(args.seed, args.output)
