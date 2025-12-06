# import streamlit as st
# import utils
# import pandas as pd

# st.set_page_config(page_title="Furnicon Store", page_icon="🛍️", layout="wide")

# st.title("🛍️ Furnicon")
# st.markdown("---")

# products = utils.get_all_products()

# if not products:
#     st.info("Inventory Empty.")
# else:
#     for item in products:
#         col_img, col_info = st.columns([0.4, 0.6])
        
#         with col_img:
#             variations = item.get("variations", [])
#             tab_labels = ["Front"] + [f"View {i+1}" for i in range(len(variations))]
#             tabs = st.tabs(tab_labels)
            
#             with tabs[0]:
#                 if "image_obj" in item: st.image(item["image_obj"], use_container_width=True)
            
#             for i, var_img in enumerate(variations):
#                 with tabs[i+1]: st.image(var_img, use_container_width=True)

#         with col_info:
#             st.subheader(item.get("title", "Product"))
#             st.caption(f"Brand: {item.get('brand', 'Generic')}")
            
#             c1, c2 = st.columns([0.3, 0.7])
#             c1.markdown(f"## ${item.get('price', 0)}")
#             c2.button("Add to Cart", key=f"btn_{item['id']}")
            
#             st.write(item.get("description", ""))
            
#             st.markdown("### Technical Details")
            
#             # The Amazon Table
#             spec_data = {
#                 "Colour": item.get("colour"),
#                 "Frame Material": item.get("frame_material"),
#                 "Style": item.get("style"),
#                 "Finish": item.get("furniture_finish"),
#                 "Seat Height": item.get("seat_height"),
#                 "Seat Width": item.get("seat_width"),
#                 "Leg Style": item.get("leg_style"),
#                 "Dimensions": item.get("dimensions_str")
#             }
#             # Filter empty
#             clean_specs = {k: v for k, v in spec_data.items() if v}
            
#             st.table(pd.DataFrame(list(clean_specs.items()), columns=["Feature", "Details"]))
            
#         st.markdown("---")


import streamlit as st
import utils
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="Furnicon Store", page_icon="🛍️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }
        .price-tag {
            font-size: 1.4rem;
            font-weight: 700;
            color: #2c3e50;
        }
        .category-tag {
            background-color: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            color: #495057;
        }
    </style>
""", unsafe_allow_html=True)

# --- 1. THE POPUP MODAL (QUICK VIEW) ---
@st.dialog("Product Specification", width="large")
def show_product_modal(item):
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        # --- FIXED GALLERY LOGIC ---
        # We collect ANY valid image source (PIL Object or URL String)
        gallery_images = []
        
        # 1. Main Image (Try Object -> Then URL)
        if item.get("image_obj"):
            gallery_images.append(("Original Source", item["image_obj"]))
        elif item.get("image_path"):
            gallery_images.append(("Main View", item["image_path"]))
            
        # 2. Variations (Try Objects -> Then URLs)
        if item.get("variations"):
            for i, var_img in enumerate(item["variations"]):
                gallery_images.append((f"AI Angle {i+1}", var_img))
        elif item.get("variation_urls"):
             for i, var_url in enumerate(item["variation_urls"]):
                gallery_images.append((f"AI Angle {i+1}", var_url))

        if not gallery_images:
            st.warning("No images available.")
        else:
            with st.container(height=500, border=False):
                for label, img in gallery_images:
                    st.image(img, caption=label, use_container_width=True)
                    st.markdown("---")

    with col2:
        st.subheader(item.get("title", "Unknown Product"))
        st.markdown(f"**Brand:** {item.get('brand', 'Generic')}")
        st.markdown(f"### ${item.get('price', 0)}")
        
        # --- FIXED DESCRIPTION ---
        # Render HTML/Markdown correctly instead of showing tags
        desc_text = item.get("description", "No description available.")
        st.markdown(desc_text, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**Technical Specs**")
        
        spec_keys = {
            "Colour": "colour",
            "Material": "frame_material",
            "Dimensions": "dimensions_str",
            "Style": "style",
            "Finish": "furniture_finish",
            "Seat Height": "seat_height"
        }
        
        table_data = {}
        for label, key in spec_keys.items():
            if item.get(key):
                table_data[label] = item[key]
        
        if table_data:
            df = pd.DataFrame(list(table_data.items()), columns=["Feature", "Value"])
            st.dataframe(df, hide_index=True, use_container_width=True)
        
        st.button("Add to Cart", type="primary", key=f"add_{item['id']}")


# --- 2. MAIN STOREFRONT GRID ---
st.title("🛍️ Furnicon Collections")
st.markdown("---")

products = utils.get_all_products()

def chunked(iterable, n):
    return [iterable[i:i + n] for i in range(0, len(iterable), n)]

if not products:
    st.info("🏪 The store is currently empty. Please initialize inventory in the Admin Bot.")
    if st.button("Go to Admin Console"):
        st.switch_page("pages/Admin_Bot.py")

else:
    rows = chunked(products, 3)
    
    for row in rows:
        cols = st.columns(3)
        for i, product in enumerate(row):
            with cols[i]:
                with st.container(border=True):
                    
                    # --- FIXED CARD IMAGE LOGIC ---
                    display_img = None
                    
                    # Priority 1: Recent AI Variation (Memory)
                    if product.get("variations"):
                        display_img = product["variations"][0]
                    # Priority 2: Original Upload (Memory)
                    elif product.get("image_obj"):
                        display_img = product["image_obj"]
                    # Priority 3: Saved Cloudinary URL (Database) <-- THIS WAS MISSING
                    elif product.get("image_path"):
                        display_img = product["image_path"]
                    
                    if display_img:
                        st.image(display_img, use_container_width=True)
                    else:
                        st.text("No Image")
                    
                    st.markdown(f"**{product.get('title', 'Untitled')}**")
                    
                    c_cat, c_brand = st.columns(2)
                    c_cat.markdown(f"<span class='category-tag'>{product.get('category', 'Furniture')}</span>", unsafe_allow_html=True)
                    c_brand.caption(f"{product.get('brand_generic', 'Generic')}")
                    
                    st.markdown(f"<div class='price-tag'>${product.get('price', 0)}</div>", unsafe_allow_html=True)
                    
                    # --- ACTIONS ROW ---
                    c_view, c_del = st.columns([0.7, 0.3])
                    
                    with c_view:
                        if st.button("Quick View", key=f"btn_{product['id']}", use_container_width=True):
                            show_product_modal(product)
                            
                    with c_del:
                        if st.button("🗑️", key=f"del_{product['id']}", use_container_width=True, help="Delete item"):
                            utils.delete_product(product['id'])
                            st.rerun()