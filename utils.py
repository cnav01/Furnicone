# import streamlit as st
# import json
# import time
# import traceback
# import base64
# from PIL import Image
# from io import BytesIO

# # --- CONFIGURATION ---
# try:
#     GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
# except (FileNotFoundError, KeyError):
#     st.error("Missing .streamlit/secrets.toml")
#     st.stop()

# try:
#     from google import genai
#     from google.genai import types
# except ImportError:
#     st.error("Library missing. Please run: pip install -r requirements.txt")
#     st.stop()

# # Initialize Client
# try:
#     client = genai.Client(api_key=GOOGLE_API_KEY)
# except Exception as e:
#     st.error(f"Client Error: {e}")
#     client = None

# # --- HELPER: ERROR LOGGER ---
# def log_error(context, error):
#     error_msg = f"❌ **Error in {context}:**\n\n{str(error)}"
#     st.session_state["global_error"] = error_msg
#     # print(f"[{context}] {error}")

# # --- HELPER: OPTIMIZE IMAGE ---
# def optimize_image(image):
#     img_copy = image.copy()
#     img_copy.thumbnail((1024, 1024))
#     if img_copy.mode in ("RGBA", "P"):
#         img_copy = img_copy.convert("RGB")
#     img_byte_arr = BytesIO()
#     img_copy.save(img_byte_arr, format='JPEG', quality=85)
#     return img_byte_arr.getvalue()

# # --- 1. TEXT ANALYST (Gemini 2.5 Flash) ---
# def analyze_image_mock(image):
#     if not client: return {}

#     try:
#         image_bytes = optimize_image(image)
        
#         prompt = """
#         Analyze this product image for an Amazon listing.
#         Return a pure JSON object with these EXACT keys:
#         {
#             "title": "SEO Product Title",
#             "description": "3-sentence technical description",
#             "brand_generic": "Suggested Brand Name",
#             "category": "General Category (e.g. Chair)",
#             "colour": "Main Color",
#             "frame_material": "Material",
#             "style": "Style",
#             "furniture_finish": "Finish",
#             "seat_height": "Height",
#             "seat_width": "Width",
#             "leg_style": "Leg Type",
#             "dimensions_str": "LxWxH cm"
#         }
#         """

#         response = client.models.generate_content(
#             model='gemini-2.5-flash',
#             contents=[
#                 types.Content(
#                     role="user",
#                     parts=[
#                         types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
#                         types.Part.from_text(text=prompt)
#                     ]
#                 )
#             ],
#             config=types.GenerateContentConfig(
#                 response_mime_type="application/json"
#             )
#         )
#         return json.loads(response.text)

#     except Exception as e:
#         log_error("Gemini 2.5 Text Analysis", e)
#         return {}

# # --- 2. IMAGE GENERATION (Gemini 2.5 Flash Image) ---
# def generate_product_variations(original_image, user_instructions=None):
#     if not client: return [original_image]

#     image_bytes = optimize_image(original_image)
#     generated_images = []
    
#     # 1. Determine Prompts
#     if user_instructions and len(user_instructions) > 0:
#         prompts = user_instructions
#     else:
#         prompts = [
#             "View from the left side profile",
#             "View from the right side profile",
#             "Close up texture detail"
#         ]

#     st.toast(f"🎨 Generating {len(prompts)} Variations (Gemini 2.5 Image)...")
    
#     # STRICTLY USING GEMINI 2.5 FLASH IMAGE
#     target_model = 'gemini-2.5-flash-image'

#     for i, user_prompt in enumerate(prompts):
        
#         full_prompt = f"Generate a photorealistic product image of THIS exact object. {user_prompt}. White background. Maintain same colors and materials. High Fidelity."
        
#         try:
#             # We attempt to send the image + text. 
#             # If 2.5-flash-image supports I2I on your tier, this works best.
#             # If it fails (400), we catch it and try text-only in the next block.
#             response = client.models.generate_content(
#                 model=target_model,
#                 contents=[
#                     types.Content(
#                         role="user",
#                         parts=[
#                             types.Part.from_text(text=full_prompt),
#                             types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
#                         ]
#                     )
#                 ],
#                 config={ "response_modalities": ["IMAGE"] }
#             )
            
#             # --- PARSING LOGIC FOR GEMINI 2.5 ---
#             # Gemini returns images in parts[].inline_data, NOT .generated_images
#             if hasattr(response, 'parts'):
#                 for part in response.parts:
#                     if part.inline_data:
#                         img_data = part.inline_data.data
#                         # Decode if it comes as a base64 string
#                         if isinstance(img_data, str):
#                             img_data = base64.b64decode(img_data)
                        
#                         img = Image.open(BytesIO(img_data))
#                         generated_images.append(img)

#         except Exception as e:
#             # If I2I fails, try Text-to-Image fallback with same model
#             # This handles cases where the model rejects the input image bytes
#             try:
#                 response = client.models.generate_content(
#                     model=target_model,
#                     contents=[
#                         types.Content(
#                             role="user",
#                             parts=[
#                                 types.Part.from_text(text=full_prompt)
#                             ]
#                         )
#                     ],
#                     config={ "response_modalities": ["IMAGE"] }
#                 )
                
#                 if hasattr(response, 'parts'):
#                     for part in response.parts:
#                         if part.inline_data:
#                             img_data = part.inline_data.data
#                             if isinstance(img_data, str):
#                                 img_data = base64.b64decode(img_data)
#                             img = Image.open(BytesIO(img_data))
#                             generated_images.append(img)
#             except Exception as e2:
#                 log_error(f"Gen Angle '{user_prompt}'", e2)

#         time.sleep(2) # Pause for rate limits

#     if not generated_images:
#         st.warning("⚠️ Generation Failed. Returning original.")
#         return [original_image]
        
#     return generated_images

# # --- 3. DATABASE ---
# def init_db():
#     if "db_products" not in st.session_state:
#         st.session_state.db_products = []

# def save_product_to_store(product_data):
#     product_data["id"] = len(st.session_state.db_products) + 1
#     st.session_state.db_products.append(product_data)

# def get_all_products():
#     return st.session_state.get("db_products", [])




# import streamlit as st
# import json
# import time
# import os
# import shutil
# import base64
# from PIL import Image
# from io import BytesIO

# # --- CONFIGURATION ---
# try:
#     GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
# except (FileNotFoundError, KeyError):
#     # Fallback for local testing if secrets not set up
#     GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# # Initialize Client
# client = None
# if GOOGLE_API_KEY:
#     try:
#         from google import genai
#         from google.genai import types
#         client = genai.Client(api_key=GOOGLE_API_KEY)
#     except ImportError:
#         pass # Handle missing lib gracefully later

# # --- DATABASE CONSTANTS ---
# DB_FILE = "furnicon_db.json"
# IMG_DIR = "furnicon_images"

# # --- HELPER: ERROR LOGGER ---
# def log_error(context, error):
#     error_msg = f"❌ **Error in {context}:**\n\n{str(error)}"
#     st.session_state["global_error"] = error_msg

# # --- HELPER: OPTIMIZE IMAGE ---
# def optimize_image(image):
#     if image.mode in ("RGBA", "P"):
#         image = image.convert("RGB")
#     img_byte_arr = BytesIO()
#     image.save(img_byte_arr, format='JPEG', quality=85)
#     return img_byte_arr.getvalue()

# # ==========================================
# #  🤖 AI CORE FUNCTIONS
# # ==========================================

# def analyze_image_mock(image):
#     if not client: 
#         return {
#             "title": "Demo Couch", "description": "AI API key missing.", 
#             "price": 999, "category": "Demo"
#         }

#     try:
#         image_bytes = optimize_image(image)
#         prompt = """
#         Analyze this product image for an Amazon listing.
#         Return a pure JSON object with these EXACT keys:
#         {
#             "title": "SEO Product Title",
#             "description": "3-sentence technical description",
#             "brand_generic": "Suggested Brand Name",
#             "category": "General Category (e.g. Chair)",
#             "colour": "Main Color",
#             "frame_material": "Material",
#             "style": "Style",
#             "furniture_finish": "Finish",
#             "seat_height": "Height",
#             "seat_width": "Width",
#             "leg_style": "Leg Type",
#             "dimensions_str": "LxWxH cm"
#         }
#         """
#         response = client.models.generate_content(
#             model='gemini-2.5-flash',
#             contents=[
#                 types.Content(
#                     role="user",
#                     parts=[
#                         types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
#                         types.Part.from_text(text=prompt)
#                     ]
#                 )
#             ],
#             config=types.GenerateContentConfig(response_mime_type="application/json")
#         )
#         return json.loads(response.text)
#     except Exception as e:
#         log_error("Gemini Text Analysis", e)
#         return {}

# def generate_product_variations(original_image, user_instructions=None):
#     if not client: return [original_image]

#     image_bytes = optimize_image(original_image)
#     generated_images = []
    
#     # default prompts
#     prompts = user_instructions if user_instructions else [
#         "View from the left side profile", 
#         "View from the right side profile", 
#         "Close up texture detail"
#     ]
    
#     st.toast(f"🎨 Generating {len(prompts)} variations (This may take 15s)...")

#     target_model = 'gemini-2.5-flash-image'

#     for i, user_prompt in enumerate(prompts):
        
#         full_prompt = f"Generate a photorealistic product image of THIS exact object. {user_prompt}. White background. Maintain same colors and materials. High Fidelity."
        
#         try:
#             time.sleep(2) # Brief pause for rate limits
            
#             response = client.models.generate_content(
#                 model=target_model,
#                 contents=[
#                     types.Content(
#                         role="user",
#                         parts=[
#                             types.Part.from_text(text=full_prompt),
#                             types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
#                         ]
#                     )
#                 ],
#                 config={ "response_modalities": ["IMAGE"] }
#             )
            
#             # --- FIX IS HERE ---
#             if hasattr(response, 'parts'):
#                 for part in response.parts:
#                     if part.inline_data:
#                         # 1. Get the data
#                         img_data = part.inline_data.data
                        
#                         # 2. Only decode if it's a string (Base64), otherwise use as-is
#                         if isinstance(img_data, str):
#                             img_data = base64.b64decode(img_data)
                        
#                         # 3. Open Image
#                         generated_images.append(Image.open(BytesIO(img_data)))
            
#         except Exception as e:
#             st.warning(f"⚠️ Angle '{user_prompt}' failed: {str(e)}")

#     if not generated_images:
#         st.error("❌ Generation failed for all angles. Returning original.")
#         return [original_image]
        
#     return generated_images


# # ==========================================
# #  💾 DATABASE & PERSISTENCE (NEW!)
# # ==========================================

# def init_db():
#     """Create data folders and load existing JSON if present."""
#     if not os.path.exists(IMG_DIR):
#         os.makedirs(IMG_DIR)
    
#     if "db_products" not in st.session_state:
#         st.session_state.db_products = []
        
#         # Load from disk
#         if os.path.exists(DB_FILE):
#             try:
#                 with open(DB_FILE, "r") as f:
#                     data_list = json.load(f)
                    
#                 # Rehydrate Images (Convert paths back to PIL Objects for the app)
#                 for item in data_list:
#                     # Load Main Image
#                     main_path = item.get("image_path")
#                     if main_path and os.path.exists(main_path):
#                         item["image_obj"] = Image.open(main_path)
                    
#                     # Load Variations
#                     var_paths = item.get("variation_paths", [])
#                     item["variations"] = []
#                     for vp in var_paths:
#                         if os.path.exists(vp):
#                             item["variations"].append(Image.open(vp))
                            
#                 st.session_state.db_products = data_list
#             except Exception as e:
#                 st.error(f"Database Error: {e}")

# def save_product_to_store(product_data):
#     """Save product metadata to JSON and images to local folder."""
#     # 1. Initialize
#     if "db_products" not in st.session_state:
#         init_db()
    
#     # 2. Assign ID
#     new_id = int(time.time()) # Use timestamp for unique ID
#     product_data["id"] = new_id
    
#     # 3. SAVE IMAGES TO DISK
#     # Save Main Image
#     main_img = product_data.get("image_obj")
#     if main_img:
#         main_filename = f"{new_id}_main.jpg"
#         main_path = os.path.join(IMG_DIR, main_filename)
#         # Convert P/RGBA to RGB
#         if main_img.mode in ("RGBA", "P"): main_img = main_img.convert("RGB")
#         main_img.save(main_path)
#         product_data["image_path"] = main_path
    
#     # Save Variations
#     var_imgs = product_data.get("variations", [])
#     var_paths = []
#     for i, img in enumerate(var_imgs):
#         var_filename = f"{new_id}_var_{i}.jpg"
#         var_path = os.path.join(IMG_DIR, var_filename)
#         if img.mode in ("RGBA", "P"): img = img.convert("RGB")
#         img.save(var_path)
#         var_paths.append(var_path)
    
#     product_data["variation_paths"] = var_paths
    
#     # 4. Clean Data for JSON (Remove non-serializable PIL objects)
#     # We create a copy to save to JSON, but keep the PIL objects in session state for immediate display
#     json_safe_data = product_data.copy()
#     if "image_obj" in json_safe_data: del json_safe_data["image_obj"]
#     if "variations" in json_safe_data: del json_safe_data["variations"]
    
#     # 5. Update Session State
#     st.session_state.db_products.append(product_data)
    
#     # 6. Write to JSON File
#     # We need to rebuild the full list of json-safe objects
#     current_db_on_disk = []
#     if os.path.exists(DB_FILE):
#         with open(DB_FILE, "r") as f:
#             try:
#                 current_db_on_disk = json.load(f)
#             except: pass
    
#     current_db_on_disk.append(json_safe_data)
    
#     with open(DB_FILE, "w") as f:
#         json.dump(current_db_on_disk, f, indent=4)

# def get_all_products():
#     if "db_products" not in st.session_state:
#         init_db()
#     return st.session_state.db_products



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

def generate_product_variations(original_image, user_instructions=None):
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

    for user_prompt in prompts:
        full_prompt = f"Generate a photorealistic product image of THIS exact object. {user_prompt}. White background. Maintain same colors and materials. High Fidelity."
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
    1. Uploads images to Cloudinary.
    2. Saves Metadata + URLs to JSON.
    """
    if "db_products" not in st.session_state:
        init_db()
    
    # 1. Assign ID
    new_id = int(time.time())
    product_data["id"] = new_id
    
    # 2. UPLOAD MAIN IMAGE
    # We prioritize the AI-generated variations if available, otherwise original
    main_pil = product_data.get("image_obj")
    
    if main_pil:
        st.toast("☁️ Uploading Main Image to Cloudinary...")
        main_url = upload_to_cloudinary(main_pil)
        if main_url:
            product_data["image_path"] = main_url # This is now a generic HTTP URL!
            st.toast("✅ Main Image Uploaded!")
    
    # 3. UPLOAD VARIATIONS (Optional but good for completeness)
    # We store these URLs in a list if you ever want to push multiple images to Shopify
    variation_urls = []
    if product_data.get("variations"):
        for i, var_img in enumerate(product_data["variations"]):
            url = upload_to_cloudinary(var_img)
            if url: variation_urls.append(url)
    product_data["variation_urls"] = variation_urls

    # 4. PREPARE FOR STORAGE
    # Remove PIL objects (cannot be saved to JSON)
    json_safe_data = product_data.copy()
    if "image_obj" in json_safe_data: del json_safe_data["image_obj"]
    if "variations" in json_safe_data: del json_safe_data["variations"]
    
    # 5. SAVE
    st.session_state.db_products.append(json_safe_data)
    
    # Update local JSON file (Snapshot)
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