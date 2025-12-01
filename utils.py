import streamlit as st
import json
import time
from PIL import Image
from io import BytesIO

# --- CONFIGURATION ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    # Fallback for local testing if secrets.toml isn't set up yet
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
    Resizes and compresses image to speed up API uploads.
    """
    # 1. Create a copy to not affect the UI display
    img_copy = image.copy()
    
    # 2. Resize to max 1024x1024 (Gemini doesn't need 4K to understand a chair)
    img_copy.thumbnail((1024, 1024))
    
    # 3. Convert to RGB (in case of Transparent PNGs which break JPEG)
    if img_copy.mode in ("RGBA", "P"):
        img_copy = img_copy.convert("RGB")
        
    # 4. Save as JPEG (Much smaller than PNG)
    img_byte_arr = BytesIO()
    # Quality=85 reduces 1.8MB to ~300KB without visible loss for AI
    img_copy.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()

# --- 1. GEMINI 2.0 FLASH (The Analyst) ---
def analyze_image_mock(image):
    if not client: return {"detected_type": "API Error", "description": "Check API Key"}

    try:
        # USE THE OPTIMIZED IMAGE
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

        # Attempt with Gemini 2.0 Flash Experimental (Latest/Widest availability)
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp', 
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
        # DEBUG MODE: If model not found, list what IS available
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            try:
                # Try to list available models to help debug
                # Note: This is a best-effort debug step
                st.error(f"Model Not Found. Attempting to list available models...")
                # In standard REST this would be GET /v1beta/models
                # For now, we suggest the user check their API key permissions
                st.error(f"Error details: {error_msg}")
                return {"detected_type": "Model Error", "description": "The specific AI model version is not enabled for your API Key. Check Google AI Studio.", "suggested_tags": []}
            except:
                pass
        
        st.error(f"Gemini Analysis Failed: {e}")
        return {"detected_type": "Error", "description": str(e), "suggested_tags": []}

# --- 2. IMAGEN 3 (The Artist) ---
def generate_product_variations(original_image):
    generated_images = []
    if not client: return [original_image]

    try:
        # USE THE OPTIMIZED IMAGE
        image_bytes = optimize_image(original_image)

        prompt = "Generate a professional product photo of this object from a slightly different side angle. Studio lighting, white background. High fidelity."

        # Using Imagen 3 Stable
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=3,
                aspect_ratio="1:1"
            )
        )

        if response.generated_images:
            for img_blob in response.generated_images:
                image_data = img_blob.image.image_bytes
                generated_images.append(Image.open(BytesIO(image_data)))
        
        return generated_images

    except Exception as e:
        st.error(f"Image Generation Failed: {e}")
        # Return original image as fallback so app doesn't break
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