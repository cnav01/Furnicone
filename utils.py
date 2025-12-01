import streamlit as st
import json
import time
from PIL import Image
from io import BytesIO

# --- CONFIGURATION ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    GOOGLE_API_KEY = "PASTE_YOUR_KEY_HERE_IF_SECRETS_FAIL"

try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error("Library missing. Please run: pip install -r requirements.txt")
    st.stop()

# Initialize Client
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
except Exception as e:
    client = None

# --- HELPER: OPTIMIZE IMAGE ---
def optimize_image(image):
    """
    Resizes and compresses image to speed up API uploads and SAVE TOKENS.
    """
    img_copy = image.copy()
    img_copy.thumbnail((800, 800)) # Reduced to save bandwidth
    if img_copy.mode in ("RGBA", "P"):
        img_copy = img_copy.convert("RGB")
    img_byte_arr = BytesIO()
    img_copy.save(img_byte_arr, format='JPEG', quality=80)
    return img_byte_arr.getvalue()

# --- 1. ROBUST ANALYST (Model Cascade) ---
def analyze_image_mock(image):
    if not client: return {"detected_type": "API Error", "description": "Check API Key"}

    image_bytes = optimize_image(image)
    
    prompt = """
    Analyze this product image for an e-commerce database.
    Return ONLY a JSON object with these keys:
    - detected_type
    - primary_material
    - color
    - description (marketing copy, approx 30 words)
    - suggested_tags (list of 5 strings)
    """

    # FALLBACK LIST: If one fails, we try the next immediately.
    # We prioritize 2.0 (Fastest), then 1.5 Flash (Stable), then 1.5 Pro (Powerful)
    models_to_try = [
        "gemini-2.0-flash-exp", 
        "gemini-1.5-flash", 
        "gemini-1.5-flash-002",
        "gemini-1.5-pro"
    ]

    last_error = None

    for model_name in models_to_try:
        try:
            # st.toast(f"Trying AI Model: {model_name}...") # Uncomment to see which model works
            response = client.models.generate_content(
                model=model_name, 
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)

        except Exception as e:
            # If error is 429 (Quota) or 404 (Not Found), just continue to next model
            error_str = str(e)
            last_error = error_str # Capture the error
            if "429" in error_str or "404" in error_str or "not found" in error_str.lower():
                continue # TRY NEXT MODEL IMMEDIATELY
            else:
                # Real error (like Auth), stop trying
                st.error(f"Critical Error on {model_name}: {e}")
                return {"detected_type": "Error", "description": str(e), "suggested_tags": []}

    # If we run out of models, show the actual error instead of "System Busy"
    error_short = str(last_error)[:100] if last_error else "Unknown Error"
    st.error(f"All AI Models failed. Details: {last_error}")
    
    return {
        "detected_type": "Analysis Failed", 
        "description": f"AI Error: {error_short}. Please check API Quota.", 
        "suggested_tags": [],
        "primary_material": "Unknown",
        "color": "Unknown"
    }

# --- 2. IMAGEN 3 (The Artist) ---
def generate_product_variations(original_image):
    if not client: return [original_image]

    try:
        image_bytes = optimize_image(original_image)
        prompt = "Generate a professional product photo of this object from a slightly different side angle. Studio lighting, white background. High fidelity."

        # Retry logic for Image Generation (Imagen 3 is strictly rate limited)
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_images(
                    model='imagen-3.0-generate-001',
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=3,
                        aspect_ratio="1:1"
                    )
                )
                generated_images = []
                if response.generated_images:
                    for img_blob in response.generated_images:
                        image_data = img_blob.image.image_bytes
                        generated_images.append(Image.open(BytesIO(image_data)))
                return generated_images
            
            except Exception as e:
                # If Quota limit, wait once then fail gracefully to original image
                if "429" in str(e) and attempt < max_retries - 1:
                    st.toast("⏳ Image Gen busy. Retrying in 5s...")
                    time.sleep(5)
                    continue
                raise e

    except Exception as e:
        # We now SHOW the error so you know why only 1 image appeared
        st.warning(f"Image Generation Skipped: {e}") 
        return [original_image]

# --- 3. DATABASE ---
def init_db():
    if "db_products" not in st.session_state:
        st.session_state.db_products = []

def save_product_to_store(product_data):
    product_data["id"] = len(st.session_state.db_products) + 1
    st.session_state.db_products.append(product_data)

def get_all_products():
    return st.session_state.get("db_products", [])