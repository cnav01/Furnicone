import streamlit as st
import json
import time
import requests # Required for Pollinations
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
    img_copy = image.copy()
    img_copy.thumbnail((800, 800))
    if img_copy.mode in ("RGBA", "P"):
        img_copy = img_copy.convert("RGB")
    img_byte_arr = BytesIO()
    img_copy.save(img_byte_arr, format='JPEG', quality=80)
    return img_byte_arr.getvalue()

# --- 1. TEXT ANALYST (STRICTLY GEMINI 2.5 FLASH) ---
def analyze_image_mock(image):
    if not client: return {"detected_type": "Config Error", "description": "API Client not initialized.", "suggested_tags": []}

    image_bytes = optimize_image(image)
    
    prompt = """
    Analyze this product image for an e-commerce database.
    Return ONLY a JSON object with these keys:
    - detected_type (e.g. 'Velvet Armchair')
    - primary_material
    - color
    - description (concise visual description, max 20 words)
    - suggested_tags (list of 5 strings)
    """

    # STRICT PRIORITY: Gemini 2.5 Flash is FIRST
    models = ["gemini-2.5-flash", "gemini-1.5-flash-002", "gemini-1.5-flash"]

    for model in models:
        try:
            response = client.models.generate_content(
                model=model, 
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception:
            continue

    return {
        "detected_type": "Analysis Failed",
        "description": "Could not connect to Google AI.",
        "suggested_tags": []
    }

# --- 2. IMAGE GENERATION (Pollinations - 60s TIMEOUT) ---
def generate_product_variations(original_image, product_description="High end furniture product"):
    """
    Uses Pollinations.ai (Flux Model).
    Increased timeout to 60s to prevent crashes on slow generations.
    """
    generated_images = []
    
    # Clean the prompt for the URL
    base_prompt = f"professional product photography of {product_description}, cinematic lighting, 8k, photorealistic, white background"
    encoded_prompt = base_prompt.replace(" ", "%20").replace(",", "%2C")
    
    st.toast(f"🎨 Furnicon is generating 3 variations (Wait ~45s)...")

    try:
        # Generate 3 variations
        for i in range(3):
            # Using 'flux' model which is high quality but slow. 
            # Added nologo=true to remove watermarks.
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&seed={i+100}&nologo=true"
            
            # FIXED: Increased timeout from 30s to 60s
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                img_bytes = BytesIO(response.content)
                img = Image.open(img_bytes)
                generated_images.append(img)
            else:
                print(f"Pollinations Error: {response.status_code}")
        
        if generated_images:
            return generated_images
            
    except Exception as e:
        st.error(f"Generation Timeout/Error: {e}")

    # Fallback: Return original if it still fails
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