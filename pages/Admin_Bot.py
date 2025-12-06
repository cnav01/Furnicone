# import streamlit as st
# import utils
# from PIL import Image
# import pandas as pd
# import io

# st.set_page_config(page_title="Admin Bot", page_icon="🍌")
# st.title("Furnicon Chat")

# # --- ERROR DASHBOARD (PERSISTENT) ---
# if "global_error" in st.session_state:
#     st.error("🚨 SYSTEM ERROR DETECTED")
#     st.warning("Please copy the text below to fix the issue:")
#     st.code(st.session_state["global_error"], language="python")
#     if st.button("Clear Error Log"):
#         del st.session_state["global_error"]
#         st.rerun()

# # --- SIDEBAR: EXPORT ACTIONS ---
# # --- SIDEBAR: EXPORT ACTIONS ---
# # --- SIDEBAR: EXPORT ACTIONS ---
# # --- SIDEBAR: EXPORT ACTIONS ---
# # --- SIDEBAR: EXPORT ACTIONS ---
# # --- SIDEBAR: EXPORT ACTIONS ---
# with st.sidebar:
#     st.header("📦 Inventory Actions")
#     products = utils.get_all_products()
#     st.metric("Total Items", len(products))
    
#     if products:
#         # OFFICIAL SHOPIFY CSV HEADERS (Standard + Unit Price Template)
#         # Reference: help.shopify.com/manual/products/import-export/using-csv
#         template_headers = [
#             "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type", "Tags", 
#             "Published", "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value", 
#             "Option3 Name", "Option3 Value", "Variant SKU", "Variant Grams", 
#             "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy", 
#             "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price", 
#             "Variant Requires Shipping", "Variant Taxable", "Variant Barcode", "Image Src", 
#             "Image Position", "Image Alt Text", "Gift Card", "SEO Title", "SEO Description", 
#             "Google Shopping / Google Product Category", "Google Shopping / Gender", 
#             "Google Shopping / Age Group", "Google Shopping / MPN", 
#             "Google Shopping / AdWords Grouping", "Google Shopping / AdWords Labels", 
#             "Google Shopping / Condition", "Google Shopping / Custom Product", 
#             "Google Shopping / Custom Label 0", "Google Shopping / Custom Label 1", 
#             "Google Shopping / Custom Label 2", "Google Shopping / Custom Label 3", 
#             "Google Shopping / Custom Label 4", "Variant Image", "Variant Weight Unit", 
#             "Tax Code", "Cost per item", "Status"
#         ]

#         csv_data = []
#         for p in products:
#             # Generate Unique Handle
#             clean_title = p.get("title", "product").replace(" ", "-").lower()
#             handle = f"{clean_title}-{p.get('id', 0)}"
            
#             # Map Internal Data to Official Shopify Headers
#             row = {
#                 "Handle": handle,
#                 "Title": p.get("title", "Untitled"),
#                 "Body (HTML)": p.get("description", ""),
#                 "Vendor": p.get("brand_generic", "Furnicon"),
#                 "Product Category": "", # Leave blank to let Shopify auto-detect
#                 "Type": p.get("category", "Furniture"),
#                 "Tags": f"{p.get('style', '')}, {p.get('frame_material', '')}, {p.get('colour', '')}",
#                 "Published": "TRUE",
#                 "Option1 Name": "Title",
#                 "Option1 Value": "Default Title",
#                 "Variant SKU": f"SKU-{p.get('id')}",
#                 "Variant Grams": 10000,
#                 "Variant Inventory Tracker": "shopify",
#                 "Variant Inventory Qty": p.get("stock", 50),
#                 "Variant Inventory Policy": "deny", # MANDATORY: 'deny' or 'continue'
#                 "Variant Fulfillment Service": "manual",
#                 "Variant Price": p.get("price", 0),
#                 "Variant Requires Shipping": "TRUE",
#                 "Variant Taxable": "TRUE",
#                 "Image Src": "", # Local paths don't work in imports (requires public URL)
#                 "Image Position": 1,
#                 "Image Alt Text": p.get("title", ""),
#                 "Gift Card": "FALSE",
#                 "Variant Weight Unit": "g",
#                 "Status": "active"
#             }
            
#             # Fill missing columns with empty strings to preserve structure
#             full_row = {header: row.get(header, "") for header in template_headers}
#             csv_data.append(full_row)
            
#         # Create DataFrame
#         df = pd.DataFrame(csv_data, columns=template_headers)
        
#         # Convert to CSV
#         csv_string = df.to_csv(index=False).encode('utf-8')
        
#         st.download_button(
#             label="📥 Export to Website",
#             data=csv_string,
#             file_name="website_import_official.csv",
#             mime="text/csv",
#             type="primary"
#         )
#     else:
#         st.caption("Add products to enable export.")
        
# # --- CHAT STATE ---
# if "messages" not in st.session_state:
#     st.session_state.messages = [{"role": "assistant", "content": "👋 Hi! Upload a product image to start."}]
# if "bot_status" not in st.session_state:
#     st.session_state.bot_status = "awaiting_upload" 
# if "draft_data" not in st.session_state:
#     st.session_state.draft_data = {}

# # --- RENDER HISTORY ---
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.write(msg["content"])
#         if msg.get("image_data"): st.image(msg["image_data"], width=250)
#         if msg.get("variations"):
#             cols = st.columns(len(msg["variations"]))
#             for i, var_img in enumerate(msg["variations"]):
#                 with cols[i]: st.image(var_img, use_container_width=True)

# # =================================================
# # STEP 1: UPLOAD IMAGE
# # =================================================
# if st.session_state.bot_status == "awaiting_upload":
#     uploaded_file = st.file_uploader("Upload Product", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
#     if uploaded_file:
#         image = Image.open(uploaded_file)
        
#         # Log User Action
#         st.session_state.messages.append({"role": "user", "content": "Here is the source image.", "image_data": image})
        
#         # Bot Analysis
#         with st.chat_message("assistant"):
#             with st.spinner("Analyzing Geometry & Specs (Gemini 2.5 Flash)..."):
#                 ai_data = utils.analyze_image_mock(image)
#                 st.session_state.draft_data = ai_data
#                 st.session_state.draft_data["image_obj"] = image
            
#             response_text = f"✅ I've analyzed the **{ai_data.get('category', 'item')}**.\n\n**How should I generate the variations?**\n\nType your instructions below (separated by commas). \n*Example: 'Front view, Rear view, Left view, Right view, Top down view, isometric view, Close up texture detail '*"
#             st.write(response_text)
            
#             st.session_state.messages.append({"role": "assistant", "content": response_text})
#             st.session_state.bot_status = "awaiting_instructions"
#             st.rerun()

# # =================================================
# # STEP 2: USER GIVES INSTRUCTIONS
# # =================================================
# if st.session_state.bot_status == "awaiting_instructions":
    
#     # Chat Input for Instructions
#     user_input = st.chat_input("e.g. Side view, Isometric view, Texture detail...")
    
#     if user_input:
#         # Log User Input
#         st.session_state.messages.append({"role": "user", "content": user_input})
        
#         with st.chat_message("assistant"):
#             # Parse Instructions
            
#             instructions = [x.strip() for x in user_input.split(',')]
#             st.write(f"👍 Generating {len(instructions)} custom shots: {', '.join(instructions)}")
            
#             # Generate
#             variations = utils.generate_product_variations(
#                 st.session_state.draft_data["image_obj"], 
#                 ai_data=st.session_state.draft_data,
#                 user_instructions=instructions
#             )
#             st.session_state.draft_data["variations"] = variations
            
#             st.write("**Here are the results:**")
#             cols = st.columns(len(variations))
#             for i, var_img in enumerate(variations):
#                 with cols[i]: st.image(var_img, use_container_width=True)
            
#             st.session_state.messages.append({
#                 "role": "assistant", 
#                 "content": "Images generated. Please verify the technical details below to publish.",
#                 "variations": variations
#             })
            
#             st.session_state.bot_status = "review_data"
#             st.rerun()

# # =================================================
# # STEP 3: DATA REVIEW & PUBLISH
# # =================================================
# if st.session_state.bot_status == "review_data":
    
#     with st.chat_message("assistant"):
#         st.write("📝 **Final Review**")
        
#         with st.form("amazon_form"):
#             title = st.text_input("Title", value=st.session_state.draft_data.get("title", ""))
#             desc = st.text_area("Description", value=st.session_state.draft_data.get("description", ""))
            
#             c1, c2 = st.columns(2)
#             price = c1.number_input("Price ($)", value=299.99)
#             stock = c2.number_input("Stock", value=50)
            
#             st.markdown("---")
            
#             # Specs
#             c1, c2 = st.columns(2)
#             colour = c1.text_input("Colour", value=st.session_state.draft_data.get("colour", ""))
#             frame = c2.text_input("Material", value=st.session_state.draft_data.get("frame_material", ""))
            
#             c3, c4 = st.columns(2)
#             dims = c3.text_input("Dimensions", value=st.session_state.draft_data.get("dimensions_str", ""))
#             brand = c4.text_input("Brand", value=st.session_state.draft_data.get("brand_generic", ""))

#             # Hidden fields preservation
#             style = st.session_state.draft_data.get("style", "")
#             finish = st.session_state.draft_data.get("furniture_finish", "")
#             seat_h = st.session_state.draft_data.get("seat_height", "")
#             seat_w = st.session_state.draft_data.get("seat_width", "")
#             legs = st.session_state.draft_data.get("leg_style", "")

#             if st.form_submit_button("Publish to Storefront 🚀"):
#                 full_data = st.session_state.draft_data
#                 full_data.update({
#                     "title": title, "price": price, "description": desc, "stock": stock,
#                     "colour": colour, "frame_material": frame, "dimensions_str": dims, "brand": brand,
#                     "style": style, "furniture_finish": finish, "seat_height": seat_h, 
#                     "seat_width": seat_w, "leg_style": legs
#                 })
                
#                 utils.save_product_to_store(full_data)
                
#                 st.session_state.messages.append({"role": "assistant", "content": "🎉 Published! You can view it in the Storefront."})
#                 st.session_state.bot_status = "done"
#                 st.rerun()

# # =================================================
# # STEP 4: DONE / LOOP
# # =================================================
# if st.session_state.bot_status == "done":
#     with st.chat_message("assistant"):
#         st.write("✅ Ready for next item.")
#         if st.button("Start Over"):
#             st.session_state.messages = [{"role": "assistant", "content": "👋 Ready. Upload image."}]
#             st.session_state.bot_status = "awaiting_upload"
#             st.session_state.draft_data = {}
#             st.rerun()


import streamlit as st
import utils
from PIL import Image
import pandas as pd

st.set_page_config(page_title="Admin Bot", page_icon="🍌")
st.title("Furnicon Chat")

# --- ERROR DASHBOARD ---
if "global_error" in st.session_state:
    st.error("🚨 SYSTEM ERROR DETECTED")
    st.code(st.session_state["global_error"], language="python")
    if st.button("Clear Error"):
        del st.session_state["global_error"]
        st.rerun()

# --- SIDEBAR: EXPORT ACTIONS ---
with st.sidebar:
    st.header("📦 Inventory Actions")
    products = utils.get_all_products()
    st.metric("Total Items", len(products))
    
    if products:
        # OFFICIAL SHOPIFY HEADERS
        template_headers = [
            "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type", "Tags", 
            "Published", "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value", 
            "Option3 Name", "Option3 Value", "Variant SKU", "Variant Grams", 
            "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy", 
            "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price", 
            "Variant Requires Shipping", "Variant Taxable", "Variant Barcode", "Image Src", 
            "Image Position", "Image Alt Text", "Gift Card", "SEO Title", "SEO Description", 
            "Google Shopping / Google Product Category", "Google Shopping / Gender", 
            "Google Shopping / Age Group", "Google Shopping / MPN", 
            "Google Shopping / AdWords Grouping", "Google Shopping / AdWords Labels", 
            "Google Shopping / Condition", "Google Shopping / Custom Product", 
            "Google Shopping / Custom Label 0", "Google Shopping / Custom Label 1", 
            "Google Shopping / Custom Label 2", "Google Shopping / Custom Label 3", 
            "Google Shopping / Custom Label 4", "Variant Image", "Variant Weight Unit", 
            "Tax Code", "Cost per item", "Status"
        ]

        csv_data = []
        for p in products:
            clean_title = p.get("title", "product").replace(" ", "-").lower()
            handle = f"{clean_title}-{p.get('id', 0)}"
            
            # --- 1. MASTER ROW (Main Product + Image 1) ---
            row = {
                "Handle": handle,
                "Title": p.get("title", "Untitled"),
                "Body (HTML)": p.get("description", ""),
                "Vendor": p.get("brand_generic", "Furnicon"),
                "Type": p.get("category", "Furniture"),
                "Tags": f"{p.get('style', '')}, {p.get('frame_material', '')}",
                "Published": "TRUE",
                "Option1 Name": "Title",
                "Option1 Value": "Default Title",
                "Variant SKU": f"SKU-{p.get('id')}",
                "Variant Grams": 10000,
                "Variant Inventory Tracker": "shopify",
                "Variant Inventory Qty": p.get("stock", 50),
                "Variant Inventory Policy": "deny",
                "Variant Fulfillment Service": "manual",
                "Variant Price": p.get("price", 0),
                "Variant Requires Shipping": "TRUE",
                "Variant Taxable": "TRUE",
                "Image Src": p.get("image_path", ""), # Main Image
                "Image Position": 1,
                "Image Alt Text": p.get("title", ""),
                "Gift Card": "FALSE",
                "Variant Weight Unit": "g",
                "Status": "active"
            }
            # Fill blanks for master row
            full_row = {header: row.get(header, "") for header in template_headers}
            csv_data.append(full_row)
            
            # --- 2. EXTRA ROWS (Additional Images) ---
            # Loop through the list of extra URLs we saved in utils.py
            extra_urls = p.get("variation_urls", [])
            
            for i, url in enumerate(extra_urls):
                # Create an empty row with just Handle + Image Info
                extra_row = {header: "" for header in template_headers}
                extra_row["Handle"] = handle
                extra_row["Image Src"] = url
                extra_row["Image Position"] = i + 2 # Start at position 2
                csv_data.append(extra_row)
            
        # Generate CSV
        df = pd.DataFrame(csv_data, columns=template_headers)
        csv_string = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Export to Shopify (Multi-Image)",
            data=csv_string,
            file_name="shopify_import_complete.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.caption("Add products to enable export.")

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
            cols = st.columns(len(msg["variations"]))
            for i, var_img in enumerate(msg["variations"]):
                with cols[i]: st.image(var_img, use_container_width=True)

# =================================================
# STEP 1: UPLOAD IMAGE
# =================================================
if st.session_state.bot_status == "awaiting_upload":
    uploaded_file = st.file_uploader("Upload Product", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.session_state.messages.append({"role": "user", "content": "Here is the source image.", "image_data": image})
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Geometry & Specs (Gemini 2.5 Flash)..."):
                ai_data = utils.analyze_image_mock(image)
                st.session_state.draft_data = ai_data
                st.session_state.draft_data["image_obj"] = image
            
            response_text = f"✅ I've analyzed the **{ai_data.get('category', 'item')}**.\n\nType instructions for variations(Front view, Rear view, Left view, Right view, Top down view, isometric view, Close up texture detail) or **'Default'**."
            st.write(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.session_state.bot_status = "awaiting_instructions"
            st.rerun()

# =================================================
# STEP 2: USER GIVES INSTRUCTIONS
# =================================================
if st.session_state.bot_status == "awaiting_instructions":
    user_input = st.chat_input("e.g. Side view, Isometric view...")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("assistant"):
            if user_input.lower() == "default":
                instructions = []
                st.write("👍 Using Standard E-Commerce Angles.")
            else:
                instructions = [x.strip() for x in user_input.split(',')]
                st.write(f"👍 Generating custom shots: {', '.join(instructions)}")
            
            with st.spinner("Rendering images (Gemini 2.5)..."):
                # Pass Data for Better Prompting
                variations = utils.generate_product_variations(
                    st.session_state.draft_data["image_obj"], 
                    ai_data=st.session_state.draft_data,
                    user_instructions=instructions
                )
                st.session_state.draft_data["variations"] = variations
            
            st.write("**Results:**")
            cols = st.columns(len(variations))
            for i, var_img in enumerate(variations):
                with cols[i]: st.image(var_img, use_container_width=True)
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Images generated. Please review.",
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
                
                # SAVE TO DB (This triggers Cloudinary Upload in utils.py)
                utils.save_product_to_store(full_data)
                
                st.session_state.messages.append({"role": "assistant", "content": "🎉 Published! Check the Storefront."})
                st.session_state.bot_status = "done"
                st.rerun()

if st.session_state.bot_status == "done":
    with st.chat_message("assistant"):
        st.write("✅ Ready for next item.")
        if st.button("Start Over"):
            st.session_state.messages = [{"role": "assistant", "content": "👋 Ready."}]
            st.session_state.bot_status = "awaiting_upload"
            st.session_state.draft_data = {}
            st.rerun()