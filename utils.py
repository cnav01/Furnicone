import streamlit as st
import json
import time
import traceback
import base64
from PIL import Image
from io import BytesIO

# --- CONFIGURATION ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    st.error("Missing .streamlit/secrets.toml")
    st.stop()

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
    st.error(f"Client Error: {e}")
    client = None

# --- HELPER: ERROR LOGGER ---
def log_error(context, error):
    error_msg = f"❌ **Error in {context}:**\n\n{str(error)}"
    st.session_state["global_error"] = error_msg
    # print(f"[{context}] {error}")

# --- HELPER: OPTIMIZE IMAGE ---
def optimize_image(image):
    img_copy = image.copy()
    img_copy.thumbnail((1024, 1024))
    if img_copy.mode in ("RGBA", "P"):
        img_copy = img_copy.convert("RGB")
    img_byte_arr = BytesIO()
    img_copy.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()

# --- 1. TEXT ANALYST (Gemini 2.5 Flash) ---
def analyze_image_mock(image):
    if not client: return {}

    try:
        image_bytes = optimize_image(image)
        
        prompt = """
        Analyze this product image for an Amazon listing.
        Return a pure JSON object with these EXACT keys:
        {
            "title": "SEO Product Title",
            "description": "3-sentence technical description",
            "brand_generic": "Suggested Brand Name",
            "category": "General Category (e.g. Chair)",
            "colour": "Main Color",
            "frame_material": "Material",
            "style": "Style",
            "furniture_finish": "Finish",
            "seat_height": "Height",
            "seat_width": "Width",
            "leg_style": "Leg Type",
            "dimensions_str": "LxWxH cm"
        }
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
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
        log_error("Gemini 2.5 Text Analysis", e)
        return {}

# --- 2. IMAGE GENERATION (Gemini 2.5 Flash Image) ---
def generate_product_variations(original_image, user_instructions=None):
    if not client: return [original_image]

    image_bytes = optimize_image(original_image)
    generated_images = []
    
    # 1. Determine Prompts
    if user_instructions and len(user_instructions) > 0:
        prompts = user_instructions
    else:
        prompts = [
            "View from the left side profile",
            "View from the right side profile",
            "Close up texture detail"
        ]

    st.toast(f"🎨 Generating {len(prompts)} Variations (Gemini 2.5 Image)...")
    
    # STRICTLY USING GEMINI 2.5 FLASH IMAGE
    target_model = 'gemini-2.5-flash-image'

    for i, user_prompt in enumerate(prompts):
        
        full_prompt = f"Generate a photorealistic product image of THIS exact object. {user_prompt}. White background. Maintain same colors and materials. High Fidelity."
        
        try:
            # We attempt to send the image + text. 
            # If 2.5-flash-image supports I2I on your tier, this works best.
            # If it fails (400), we catch it and try text-only in the next block.
            response = client.models.generate_content(
                model=target_model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=full_prompt),
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                        ]
                    )
                ],
                config={ "response_modalities": ["IMAGE"] }
            )
            
            # --- PARSING LOGIC FOR GEMINI 2.5 ---
            # Gemini returns images in parts[].inline_data, NOT .generated_images
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if part.inline_data:
                        img_data = part.inline_data.data
                        # Decode if it comes as a base64 string
                        if isinstance(img_data, str):
                            img_data = base64.b64decode(img_data)
                        
                        img = Image.open(BytesIO(img_data))
                        generated_images.append(img)

        except Exception as e:
            # If I2I fails, try Text-to-Image fallback with same model
            # This handles cases where the model rejects the input image bytes
            try:
                response = client.models.generate_content(
                    model=target_model,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=full_prompt)
                            ]
                        )
                    ],
                    config={ "response_modalities": ["IMAGE"] }
                )
                
                if hasattr(response, 'parts'):
                    for part in response.parts:
                        if part.inline_data:
                            img_data = part.inline_data.data
                            if isinstance(img_data, str):
                                img_data = base64.b64decode(img_data)
                            img = Image.open(BytesIO(img_data))
                            generated_images.append(img)
            except Exception as e2:
                log_error(f"Gen Angle '{user_prompt}'", e2)

        time.sleep(2) # Pause for rate limits

    if not generated_images:
        st.warning("⚠️ Generation Failed. Returning original.")
        return [original_image]
        
    return generated_images

# --- 3. DATABASE ---
def init_db():
    if "db_products" not in st.session_state:
        st.session_state.db_products = []

def save_product_to_store(product_data):
    product_data["id"] = len(st.session_state.db_products) + 1
    st.session_state.db_products.append(product_data)

def get_all_products():
    return st.session_state.get("db_products", [])