import streamlit as st
import utils
from PIL import Image
import pandas as pd

st.set_page_config(page_title="Admin Bot", page_icon="🍌")
st.title("Furnicon Chat")

# --- ERROR DASHBOARD (PERSISTENT) ---
if "global_error" in st.session_state:
    st.error("🚨 SYSTEM ERROR DETECTED")
    st.warning("Please copy the text below to fix the issue:")
    st.code(st.session_state["global_error"], language="python")
    if st.button("Clear Error Log"):
        del st.session_state["global_error"]
        st.rerun()

# --- CHAT STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "👋 Hi! Upload a product image to start."}]
if "bot_status" not in st.session_state:
    st.session_state.bot_status = "awaiting_upload" 
if "draft_data" not in st.session_state:
    st.session_state.draft_data = {}

# --- RENDER HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("image_data"): st.image(msg["image_data"], width=250)
        if msg.get("variations"):
            cols = st.columns(3)
            for i, var_img in enumerate(msg["variations"]):
                with cols[i]: st.image(var_img, use_container_width=True)

# =================================================
# STEP 1: UPLOAD IMAGE
# =================================================
if st.session_state.bot_status == "awaiting_upload":
    uploaded_file = st.file_uploader("Upload Product", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        
        # Log User Action
        st.session_state.messages.append({"role": "user", "content": "Here is the source image.", "image_data": image})
        
        # Bot Analysis
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Geometry & Specs (Gemini 2.5 Flash)..."):
                ai_data = utils.analyze_image_mock(image)
                st.session_state.draft_data = ai_data
                st.session_state.draft_data["image_obj"] = image
            
            response_text = f"✅ I've analyzed the **{ai_data.get('category', 'item')}**.\n\n**How should I generate the variations?**\n\nType your instructions below (separated by commas). \n*Example: 'Top view, Back view, Zoom on leg'* \n\nOr just type **'Default'** for standard angles."
            st.write(response_text)
            
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.session_state.bot_status = "awaiting_instructions"
            st.rerun()

# =================================================
# STEP 2: USER GIVES INSTRUCTIONS
# =================================================
if st.session_state.bot_status == "awaiting_instructions":
    
    # Chat Input for Instructions
    user_input = st.chat_input("e.g. Side view, Isometric view, Texture detail...")
    
    if user_input:
        # Log User Input
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("assistant"):
            # Parse Instructions
            if user_input.lower() == "default":
                instructions = [] # Will trigger default in utils
                st.write("👍 Using Standard E-Commerce Angles.")
            else:
                instructions = [x.strip() for x in user_input.split(',')]
                st.write(f"👍 Generating {len(instructions)} custom shots: {', '.join(instructions)}")
            
            # Generate
            with st.spinner("Rendering images (Gemini 2.5 Flash Image)..."):
                variations = utils.generate_product_variations(
                    st.session_state.draft_data["image_obj"], 
                    user_instructions=instructions
                )
                st.session_state.draft_data["variations"] = variations
            
            st.write("**Here are the results:**")
            cols = st.columns(3)
            for i, var_img in enumerate(variations):
                with cols[i]: st.image(var_img, use_container_width=True)
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Images generated. Please verify the technical details below to publish.",
                "variations": variations
            })
            
            st.session_state.bot_status = "review_data"
            st.rerun()

# =================================================
# STEP 3: DATA REVIEW & PUBLISH
# =================================================
if st.session_state.bot_status == "review_data":
    
    with st.chat_message("assistant"):
        st.write("📝 **Final Review**")
        
        with st.form("amazon_form"):
            title = st.text_input("Title", value=st.session_state.draft_data.get("title", ""))
            desc = st.text_area("Description", value=st.session_state.draft_data.get("description", ""))
            
            c1, c2 = st.columns(2)
            price = c1.number_input("Price ($)", value=299.99)
            stock = c2.number_input("Stock", value=50)
            
            st.markdown("---")
            
            # Specs
            c1, c2 = st.columns(2)
            colour = c1.text_input("Colour", value=st.session_state.draft_data.get("colour", ""))
            frame = c2.text_input("Material", value=st.session_state.draft_data.get("frame_material", ""))
            
            c3, c4 = st.columns(2)
            dims = c3.text_input("Dimensions", value=st.session_state.draft_data.get("dimensions_str", ""))
            brand = c4.text_input("Brand", value=st.session_state.draft_data.get("brand_generic", ""))

            # Hidden fields preservation
            style = st.session_state.draft_data.get("style", "")
            finish = st.session_state.draft_data.get("furniture_finish", "")
            seat_h = st.session_state.draft_data.get("seat_height", "")
            seat_w = st.session_state.draft_data.get("seat_width", "")
            legs = st.session_state.draft_data.get("leg_style", "")

            if st.form_submit_button("Publish to Storefront 🚀"):
                full_data = st.session_state.draft_data
                full_data.update({
                    "title": title, "price": price, "description": desc, "stock": stock,
                    "colour": colour, "frame_material": frame, "dimensions_str": dims, "brand": brand,
                    "style": style, "furniture_finish": finish, "seat_height": seat_h, 
                    "seat_width": seat_w, "leg_style": legs
                })
                
                utils.save_product_to_store(full_data)
                
                st.session_state.messages.append({"role": "assistant", "content": "🎉 Published! You can view it in the Storefront."})
                st.session_state.bot_status = "done"
                st.rerun()

# =================================================
# STEP 4: DONE / LOOP
# =================================================
if st.session_state.bot_status == "done":
    with st.chat_message("assistant"):
        st.write("✅ Ready for next item.")
        if st.button("Start Over"):
            st.session_state.messages = [{"role": "assistant", "content": "👋 Ready. Upload image."}]
            st.session_state.bot_status = "awaiting_upload"
            st.session_state.draft_data = {}
            st.rerun()