import streamlit as st
import json
import time
import os
import base64
from PIL import Image
from io import BytesIO

# --- IMPORTS FOR CLOUDINARY ---
import cloudinary
import cloudinary.uploader
import cloudinary.api

# --- CONFIGURATION & SECRETS ---
try:
    # 1. Setup Google Gemini
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    
    # 2. Setup Cloudinary
    cloudinary.config( 
        cloud_name = st.secrets["cloudinary"]["cloud_name"], 
        api_key = st.secrets["cloudinary"]["api_key"], 
        api_secret = st.secrets["cloudinary"]["api_secret"],
        secure = True
    )
except (FileNotFoundError, KeyError):
    # Fallback for local dev if secrets aren't set yet
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Initialize Gemini Client
client = None
if GOOGLE_API_KEY:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GOOGLE_API_KEY)
    except ImportError:
        pass 

# --- CONSTANTS ---
DB_FILE = "furnicon_db.json"

# --- HELPER: OPTIMIZE IMAGE ---
def optimize_image(image):
    """Converts PIL image to Bytes for API calls."""
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()

# ==========================================
#  ☁️ CLOUDINARY UPLOAD (The New Part)
# ==========================================
def upload_to_cloudinary(image_obj, folder="furnicon_inventory"):
    """
    Uploads a PIL Image to Cloudinary and returns the secure public URL.
    """
    try:
        # Convert PIL to Bytes for upload
        img_bytes = optimize_image(image_obj)
        
        # Upload
        response = cloudinary.uploader.upload(
            img_bytes, 
            folder=folder,
            resource_type="image"
        )
        
        # Return the 'secure_url' (https)
        return response.get("secure_url")
        
    except Exception as e:
        st.error(f"☁️ Cloudinary Upload Error: {e}")
        return None

# ==========================================
#  🤖 AI CORE FUNCTIONS
# ==========================================

def analyze_image_mock(image):
    if not client: return {"title": "Demo Item", "description": "No API Key"}

    try:
        image_bytes = optimize_image(image)
        prompt = """
        Analyze this product image for an Amazon/Shopify listing.
        Return a pure JSON object with these EXACT keys:
        {
            "title": "SEO Product Title",
            "description": "Compelling marketing description (HTML allowed)",
            "brand_generic": "Suggested Brand Name",
            "category": "Product Type (e.g. Chair)",
            "colour": "Dominant Color",
            "frame_material": "Material",
            "style": "Design Style",
            "furniture_finish": "Finish",
            "seat_height": "Height",
            "seat_width": "Width",
            "leg_style": "Leg Type",
            "dimensions_str": "LxWxH"
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
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"AI Analysis Error: {e}")
        return {}

def generate_product_variations(original_image, ai_data= None, user_instructions=None):
    if not client: return [original_image]

    image_bytes = optimize_image(original_image)
    generated_images = []
    
    prompts = user_instructions if user_instructions else [
        "View from the left side profile", 
        "View from the right side profile", 
        "Close up texture detail"
    ]
    
    st.toast(f"🎨 Rendering {len(prompts)} angles with Gemini 2.5...")

    target_model = 'gemini-2.5-flash-image'
    anchor_text = ""
    if ai_data:
        anchor_text = f"The object is a {ai_data.get('style', '')} {ai_data.get('category', 'furniture')} made of {ai_data.get('frame_material', '')} with {ai_data.get('colour', '')} finish."

    for user_prompt in prompts:
        full_prompt = f"""
        Crucial instruction: Maintain strict geometric consistency with the reference image.
        {anchor_text}
        Generate a photorealistic {user_prompt} of this exact item. 
        Preserve exact textures and structural details. Solid white background.
        """
        try:
            time.sleep(2) # Rate limit protection
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
            
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if part.inline_data:
                        img_data = part.inline_data.data
                        if isinstance(img_data, str):
                            img_data = base64.b64decode(img_data)
                        generated_images.append(Image.open(BytesIO(img_data)))
            
        except Exception as e:
            st.warning(f"⚠️ Angle '{user_prompt}' skipped: {str(e)}")

    if not generated_images:
        return [original_image]
        
    return generated_images

# ==========================================
#  💾 DATABASE & PERSISTENCE
# ==========================================

def init_db():
    if "db_products" not in st.session_state:
        st.session_state.db_products = []
        
        # Load from disk if available (Persistence)
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    # When loading from disk, we trust the URLs are valid
                    st.session_state.db_products = json.load(f)
            except:
                pass

def save_product_to_store(product_data):
    """
    1. Uploads Main Image + All Variations to Cloudinary.
    2. Saves to JSON.
    """
    if "db_products" not in st.session_state:
        init_db()
    
    # 1. Assign ID
    new_id = int(time.time())
    product_data["id"] = new_id
    
    # 2. UPLOAD MAIN IMAGE (Priority: Variation 0, else Original)
    main_pil = None
    if product_data.get("variations"):
        main_pil = product_data["variations"][0]
    else:
        main_pil = product_data.get("image_obj")
    
    if main_pil:
        st.toast("☁️ Uploading Main Image...")
        main_url = upload_to_cloudinary(main_pil)
        if main_url:
            product_data["image_path"] = main_url
            st.toast("✅ Main Image Uploaded!")
        else:
            product_data["image_path"] = ""
    
    # 3. UPLOAD REMAINING VARIATIONS (New Active Code)
    variation_urls = []
    # Check if we have more than 1 variation
    if product_data.get("variations") and len(product_data["variations"]) > 1:
        st.toast(f"☁️ Uploading {len(product_data['variations'])-1} extra angles...")
        
        # Loop through variations starting from index 1 (skip 0)
        for i, var_img in enumerate(product_data["variations"][1:]):
            url = upload_to_cloudinary(var_img)
            if url: 
                variation_urls.append(url)
                
    product_data["variation_urls"] = variation_urls

    # 4. SAVE TO DB
    json_safe_data = product_data.copy()
    if "image_obj" in json_safe_data: del json_safe_data["image_obj"]
    if "variations" in json_safe_data: del json_safe_data["variations"]
    
    st.session_state.db_products.append(json_safe_data)
    
    try:
        with open(DB_FILE, "w") as f:
            json.dump(st.session_state.db_products, f, indent=4)
    except Exception as e:
        print(f"JSON Save Error: {e}")

def get_all_products():
    if "db_products" not in st.session_state:
        init_db()
    return st.session_state.db_products

# --- ADD THIS TO utils.py ---

def delete_product(product_id):
    """Removes a product from session state and JSON DB."""
    # 1. Remove from Session State
    if "db_products" in st.session_state:
        st.session_state.db_products = [
            p for p in st.session_state.db_products if p.get("id") != product_id
        ]
    
    # 2. Overwrite JSON File
    try:
        with open(DB_FILE, "w") as f:
            json.dump(st.session_state.db_products, f, indent=4)
    except Exception as e:
        st.error(f"Error deleting: {e}")