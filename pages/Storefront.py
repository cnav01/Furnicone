import streamlit as st
import utils

st.set_page_config(page_title="Storefront", page_icon="🛍️", layout="wide")

st.title("🛍️ Furniture Store")

products = utils.get_all_products()

if not products:
    st.info("Store is empty. Go to Admin Bot to add items.")
else:
    cols = st.columns(3)
    for idx, item in enumerate(products):
        with cols[idx % 3]:
            with st.container(border=True):
                if "image_obj" in item:
                    st.image(item["image_obj"], use_column_width=True)
                st.subheader(item["title"])
                st.write(f"**${item['price']}**")
                st.caption(f"Dimensions: {item['dims']}")
                st.button("Add to Cart", key=idx)