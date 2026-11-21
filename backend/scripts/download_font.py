import urllib.request
import os

url = "https://github.com/google/fonts/raw/main/ofl/notosansdevanagari/NotoSansDevanagari-Regular.ttf"
os.makedirs("C:/Users/Hitika/Desktop/proje/backend/assets", exist_ok=True)
try:
    print("Downloading font...")
    urllib.request.urlretrieve(url, "C:/Users/Hitika/Desktop/proje/backend/assets/NotoSansDevanagari-Regular.ttf")
    print("Font downloaded successfully.")
except Exception as e:
    print(f"Error downloading font: {e}")
