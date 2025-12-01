import streamlit as st
import utils
from PIL import Image

st.set_page_config(page_title="Admin Bot", page_icon="🍌")

st.title("🍌 Nano Banana: Asset Processor")

# State for Step 1 vs Step 2
if "step" not in st.session_state:
    st.session_state.step = 1
if "draft_data" not in st.session_state:
    st.session_state.draft_data = {}

# --- STEP 1: UPLOAD ---
if st.session_state.step == 1:
    st.header("1. Ingest Product")
    uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, width=300)
        
        if st.button("Analyze with AI 🧠"):
            with st.spinner("Scanning..."):
                results = utils.analyze_image_mock(image)
                st.session_state.draft_data = results
                st.session_state.draft_data["image_obj"] = image
                st.session_state.step = 2
                st.rerun()

# --- STEP 2: VERIFY & PUBLISH ---
if st.session_state.step == 2:
    st.header("2. Verify & Publish")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("AI Findings")
        st.write(f"**Type:** {st.session_state.draft_data['detected_type']}")
        st.write(f"**Material:** {st.session_state.draft_data['primary_material']}")
        st.image(st.session_state.draft_data["image_obj"], width=200)
        
    with col2:
        st.warning("⚠️ Input Dimensions Required")
        with st.form("pub_form"):
            title = st.text_input("Title", value="New Product")
            price = st.number_input("Price ($)", value=100.0)
            h = st.number_input("Height (cm)")
            w = st.number_input("Width (cm)")
            d = st.number_input("Depth (cm)")
            
            if st.form_submit_button("🚀 Publish to Website"):
                if h > 0 and w > 0:
                    st.session_state.draft_data["title"] = title
                    st.session_state.draft_data["price"] = price
                    st.session_state.draft_data["dims"] = f"{h}x{w}x{d} cm"
                    
                    utils.save_product_to_store(st.session_state.draft_data)
                    st.success("Published!")
                    
                    if st.button("Next Item"):
                        st.session_state.step = 1
                        st.rerun()
                else:
                    st.error("Dimensions cannot be zero.")