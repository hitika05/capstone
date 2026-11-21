import os
import sys
from dotenv import load_dotenv

# Add backend/services to path
sys.path.append(os.path.join(os.getcwd(), "backend", "services"))

from ai_service import extract_business_details, generate_prompt, generate_image

load_dotenv(dotenv_path="backend/.env")

def test_autonomous_pipeline(prompt, label="Test"):
    print(f"\n--- Testing: {label} ---")
    try:
        # 1. Extraction
        print("1. Extracting details...")
        data = extract_business_details(prompt)
        print(f"   Business Name: {data.get('businessName')}")
        print(f"   Layout Type: {data.get('layoutType')}")
        print(f"   Tagline: {data.get('tagline')}")
        
        # 2. Prompt Generation
        print("2. Generating visual prompt...")
        v_prompt = generate_prompt(data.get("visualTheme", "aesthetic background"))
        print(f"   Visual Prompt: {v_prompt}")
        
        # 3. Image Generation (Optional: Skip if key is expensive, but we should test once)
        # print("3. Generating image...")
        # img_path = generate_image(v_prompt)
        # print(f"   Image saved to: {img_path}")
        
        return True
    except Exception as e:
        print(f"   FAILED: {e}")
        return False

if __name__ == "__main__":
    # Test 1: The "Chham Chham" Bangle Prompt
    test_1 = "मैं चूड़ियाँ भेजती हूं और मेरी दुकान का नाम है छम छम और उसकी टैगलाइन है रंग बिरंगी चूड़ियाँ इसके लिए एक इंस्टाग्राम ऐड बनाए जिसके बैकग्राउंड में एक भारतीय नारी ने चूड़ियाँ पहनी हुई हो"
    
    # Test 2: Obscure Niche
    test_2 = "My name is Orbit and I fix Satellite Antennae. We offer high speed internet setup and repair."

    test_autonomous_pipeline(test_1)
    test_autonomous_pipeline(test_2)
