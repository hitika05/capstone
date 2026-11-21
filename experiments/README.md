# VoiceDesign AI evaluation experiments

This folder contains evaluation scripts and datasets for the VoiceDesign AI project. All generated data is draft material and should be treated as `needs_human_review` before publication.

## Code locations and implementation notes

The repository layout here differs slightly from the prompt description:

- Speech-to-text and extraction live in [backend/services/ai_service.py](../backend/services/ai_service.py)
- Intent parsing and brand memory live in [backend/services/pipeline_service.py](../backend/services/pipeline_service.py)
- The UI Review & Edit flow lives in [frontend/src/App.jsx](../frontend/src/App.jsx)

### 1) Speech-to-text
- Function: `transcribe_audio` in [backend/services/ai_service.py](../backend/services/ai_service.py)
- STT provider selection: `os.getenv("STT_PROVIDER", "native_google")` and the code branches for `local_whisper`, `openai_api`, and Google SpeechRecognition
- Default behavior: Google SpeechRecognition
- Optional local Whisper: `import whisper; whisper.load_model(...)`
- Optional API provider: OpenAI-compatible transcription endpoint

### 2) Rule-based review intent parser
- Function: `keyword_intent_parser` in [backend/services/pipeline_service.py](../backend/services/pipeline_service.py)
- Used in review mode: `parse_intent(text, mode="review")`
- It matches signals like `price`, `festival`, `banner`, `logo`, and business-specific keywords for bakery, tailor, beauty, mobile, yoga, etc.

### 3) BERT-style final intent classifier
- Function: `multilingual_bert_parser` in [backend/services/pipeline_service.py](../backend/services/pipeline_service.py)
- Used in final mode: `parse_intent(text, mode="final")`
- Prediction target: `DESIGN_TYPES` (`instagram_post`, `logo`, `festival_post`, `banner`, `price_list_flyer`)
- Model checkpoint: `os.getenv("INTENT_MODEL_ID", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")`
- It is not trained in this repo; it is a zero-shot Hugging Face model loaded at runtime if the package is available.

### 4) Prompt builder
- Function: `build_prompt_package` in [backend/services/pipeline_service.py](../backend/services/pipeline_service.py)
- It turns structured fields such as business, mood, color, and brand memory into a generated English prompt and negative prompt.
- The backend then routes image generation through `generate_routed_designs`.

### 5) Image generation and backend routing
- Function: `generate_image` in [backend/services/ai_service.py](../backend/services/ai_service.py)
- Backend logic: if `STABILITY_API_KEY` is present, it calls the Stability API; otherwise it falls back to the Pollinations free image generator; if both fail, it uses a local PNG placeholder.
- The UI does not include the actual backend name in the image metadata, so the easiest runtime signal is the file-generation path and request behavior; the code logs when the Stability API is used and swaps to fallback when it fails.
- Image URLs served by FastAPI come from `backend/main.py` via the `/generations` static route.

### 6) Devanagari overlay
- The app renders overlay text in the browser; it does not do a server-side Devanagari overlay in the same way that the prompt suggests.
- The code that handles visual text and translation is in [backend/main.py](../backend/main.py) and the design logic is in the frontend [frontend/src/App.jsx](../frontend/src/App.jsx) and the design viewer component in [frontend/src/components/DesignViewer.jsx](../frontend/src/components/DesignViewer.jsx).
- Pillow is used in the local fallback background generation, not necessarily for production overlay text; the Devanagari text path is not a dedicated OCR/overlay pipeline in the current codebase.

### 7) Price list extractor and template
- Price list extraction is implemented in the backend image prompt logic and the frontend price-list mode in [frontend/src/App.jsx](../frontend/src/App.jsx)
- The extraction logic is primarily regex + intent matching in [backend/services/ai_service.py](../backend/services/ai_service.py), and the pricing route is part of the generated design pipeline in [backend/services/pipeline_service.py](../backend/services/pipeline_service.py).

### 8) Brand memory
- Function: `load_brand_memory` and `save_brand_memory` in [backend/services/pipeline_service.py](../backend/services/pipeline_service.py)
- Firestore path: optional Firebase Admin integration when `FIREBASE_CREDENTIALS_PATH` exists
- Fallback: local JSON file at `backend/assets/brand_memory.json`

### Mismatch with the original prompt
- The code does not contain a custom fine-tuned Whisper model.
- It does not include a dedicated Devanagari-on-image server-side text renderer with Pillow overlay as a separate module.
- The image generation backend is Stability API first, then Pollinations fallback, then local placeholder.
- The project path names differ from the prompt; files live under `backend/services` instead of root-level `backend/` modules.

## Execution notes

The smoke tests in this folder intentionally use a small `--limit` parameter to avoid heavy model runs and to keep the project runnable on a single machine.

All data prepared under `experiments/data/` is draft material and `needs_human_review` before inclusion in any paper results.
