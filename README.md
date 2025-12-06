# 🛋️ Furnicon: AI-Powered Furniture Operations

Furnicon is an internal tool for furniture retailers that automates the product digitization workflow. It uses **Google Gemini 2.5 Multimodal AI** to ingest raw photos, generate technical specifications, render multi-angle marketing assets, and prepare inventory for Shopify.

## 🚀 Key Features

* **Admin Console:** Upload raw furniture images to extract metadata (Dimensions, Material, Style) using **Gemini 2.5 Flash**.
* **AI Photography Studio:** Automatically generates 3+ marketing angles (Side, Top, Texture) from a single photo using **Gemini 2.5 Flash Image**.
* **Cloud Asset Management:** Automatically uploads generated assets to **Cloudinary** for permanent, public hosting.
* **Digital Storefront:** A responsive grid-layout gallery to preview the customer experience.
* **Shopify Integration:** One-click export of inventory (with public image URLs) to Shopify-compliant CSV format.

## 🛠️ Tech Stack

* **Frontend:** Streamlit (Custom Enterprise Theme)
* **AI Core:** Google GenAI SDK (Gemini 2.5 Flash & Flash-Image)
* **Storage:** Cloudinary (Image Hosting) + Local JSON (Metadata)
* **Data Processing:** Pandas (ETL for Shopify Export)

## ⚙️ Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/furnicon.git](https://github.com/yourusername/furnicon.git)
    cd furnicon
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Secrets:**
    Create a `.streamlit/secrets.toml` file with your API keys:
    ```toml
    GOOGLE_API_KEY = "your_google_ai_key"

    [cloudinary]
    cloud_name = "your_cloud_name"
    api_key = "your_api_key"
    api_secret = "your_api_secret"
    ```

4.  **Run the App:**
    ```bash
    streamlit run app.py
    ```

## 📦 Shopify Export Workflow
1.  Use the **Admin Bot** to generate product listings.
2.  Click **"Publish"** (images are auto-uploaded to Cloudinary).
3.  Go to the Sidebar and click **"Export to Shopify"**.
4.  Import the CSV directly into your Shopify Admin panel.

---
*Built for the Furniture Tech Industry.*