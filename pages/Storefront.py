import streamlit as st
import utils

st.set_page_config(page_title="Live Store", page_icon="🛍️", layout="wide")

st.title("🛍️ Modern Furniture Store")
st.caption("Live view of the 'db_products' database")

# 1. Fetch data from utils
products = utils.get_all_products()

# 2. Check if empty
if not products:
    st.container(border=True).info("🏪 The store is currently empty. Please go to the **Admin Bot** to ingest new inventory.")
else:
    # 3. Render Grid
    cols = st.columns(3) # 3 columns wide
    
    for index, item in enumerate(products):
        with cols[index % 3]:
            with st.container(border=True):
                # Image
                if "image_obj" in item:
                    st.image(item["image_obj"], use_column_width=True)
                
                # Title & Price
                # Use .get() to prevent errors if keys are missing
                title = item.get("title", "Untitled Product")
                price = item.get("price", 0.00)
                
                st.subheader(title)
                st.markdown(f"### ${price}")
                
                # Metadata
                # FIX: We now look for 'dimensions_str' to match the Admin Bot
                dims = item.get("dimensions_str", "Dimensions N/A")
                mat = item.get("primary_material", "Material N/A")
                
                st.text(f"Dimensions: {dims}")
                st.text(f"Material: {mat}")
                
                # Tags
                tags = item.get("suggested_tags", [])
                if tags:
                    st.caption(", ".join(tags))
                
                st.button("Add to Cart 🛒", key=f"cart_{index}", type="primary", use_container_width=True)