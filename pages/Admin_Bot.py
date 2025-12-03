import streamlit as st
import utils
from PIL import Image

st.set_page_config(page_title="Admin Bot", page_icon="🍌")

st.title("🍌 Nano Banana Chat")

# --- CHAT HISTORY & STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hi! I'm Nano Banana. Upload a product image to start."}
    ]
if "bot_status" not in st.session_state:
    st.session_state.bot_status = "awaiting_upload" 
if "draft_data" not in st.session_state:
    st.session_state.draft_data = {}

# --- RENDER HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("image_data"):
            st.image(msg["image_data"], width=250)
        if msg.get("variations"):
            st.write("**Generated Variations:**")
            cols = st.columns(3)
            for i, var_img in enumerate(msg["variations"]):
                with cols[i]:
                    st.image(var_img, use_container_width=True)

# --- LOGIC ---

# 1. IMAGE UPLOAD
if st.session_state.bot_status == "awaiting_upload":
    uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        
        st.session_state.messages.append({
            "role": "user", "content": "Here is the product.", "image_data": image
        })
        
        with st.chat_message("assistant"):
            # A. Vision Analysis
            with st.spinner("Gemini is extracting details..."):
                ai_data = utils.analyze_image_mock(image)
                st.session_state.draft_data = ai_data
                st.session_state.draft_data["image_obj"] = image
            
            # B. Image Generation (Using Pollinations)
            # We construct a prompt using the data Gemini just found
            # e.g. "Teal Velvet Lounge Chair"
            desc_for_gen = f"{ai_data.get('color', '')} {ai_data.get('primary_material', '')} {ai_data.get('detected_type', 'furniture')}"
            
            with st.spinner("Generating variations (Free Engine)..."):
                variations = utils.generate_product_variations(image, product_description=desc_for_gen)
                st.session_state.draft_data["variations"] = variations
            
            # Response
            desc = ai_data.get('description', 'No description')
            response_text = f"✅ Analysis Complete.\n\n**Type:** {ai_data.get('detected_type')}\n**Material:** {ai_data.get('primary_material')}\n\n**Description:** {desc}\n\nI have generated {len(variations)} variations below using the Free Engine."
            st.write(response_text)
            
            # Show variations immediately
            cols = st.columns(3)
            for i, var_img in enumerate(variations):
                with cols[i]:
                    st.image(var_img, use_container_width=True, caption=f"Gen {i+1}")

            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_text,
                "variations": variations
            })
            
            st.session_state.bot_status = "awaiting_dims"
            st.rerun()

# 2. DIMENSION FORM
if st.session_state.bot_status == "awaiting_dims":
    with st.chat_message("assistant"):
        st.write("📝 **Final Details**")
        with st.form("chat_form"):
            title = st.text_input("Title", value=f"AI {st.session_state.draft_data.get('detected_type', 'Product')}")
            price = st.number_input("Price ($)", value=199.99)
            c1, c2, c3 = st.columns(3)
            h = c1.number_input("H (cm)", min_value=1)
            w = c2.number_input("W (cm)", min_value=1)
            d = c3.number_input("D (cm)", min_value=1)
            
            if st.form_submit_button("Publish 🚀"):
                st.session_state.draft_data["title"] = title
                st.session_state.draft_data["price"] = price
                st.session_state.draft_data["dimensions_str"] = f"{h}x{w}x{d} cm"
                
                utils.save_product_to_store(st.session_state.draft_data)
                
                msg = "🎉 Product is LIVE on the Storefront."
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.session_state.bot_status = "done"
                st.rerun()

# 3. RESET
if st.session_state.bot_status == "done":
    with st.chat_message("assistant"):
        st.write("🎉 Product is LIVE.")
        if st.button("Start New"):
            st.session_state.messages = [{"role": "assistant", "content": "👋 Ready."}]
            st.session_state.bot_status = "awaiting_upload"
            st.session_state.draft_data = {}
            st.rerun()