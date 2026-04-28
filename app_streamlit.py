import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from core.scraper import ScraperOrchestrator
from config import OUTPUT_DIR, OLLAMA_MODEL, OLLAMA_HOST, SCRAPERAPI_KEY, SCRAPINGBEE_KEY
import requests
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="SmartScraper AI",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Styling & Animations ---
st.markdown("""
    <style>
    /* Color Palette */
    :root {
        --primary-color: #6C63FF;
        --secondary-color: #4CAF50;
        --bg-color: #F0F2F6;
        --text-color: #262730;
        --accent-color: #FF4B4B;
    }

    /* Fade-in Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stApp {
        background-color: var(--bg-color);
    }

    .main .block-container {
        animation: fadeIn 0.8s ease-out;
    }

    /* Card Styling */
    .card {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease;
    }

    .card:hover {
        transform: scale(1.01);
    }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(135deg, #6C63FF 0%, #4B45E5 100%);
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3);
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #4B45E5 0%, #3A35C2 100%);
        box-shadow: 0 6px 20px rgba(108, 99, 255, 0.4);
        transform: translateY(-2px);
    }

    /* Input Styling */
    .stTextArea>div>div>textarea {
        border-radius: 12px;
        border: 2px solid #eee;
        transition: border-color 0.3s;
    }

    .stTextArea>div>div>textarea:focus {
        border-color: var(--primary-color);
    }

    /* Sidebar Branding */
    [data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #e0e0e0;
    }

    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--primary-color);
        margin-bottom: 1rem;
        text-align: center;
    }

    /* Status Indicators */
    .status-dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
    }
    .status-online { background-color: #4CAF50; box-shadow: 0 0 8px #4CAF50; }
    .status-offline { background-color: #FF4B4B; box-shadow: 0 0 8px #FF4B4B; }

    </style>
    """, unsafe_allow_html=True)

def check_ollama():
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    # --- Sidebar ---
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🕸️ SmartScraper AI</div>', unsafe_allow_html=True)
        st.markdown("---")

        page = st.radio("Navigate", ["🚀 Scraper", "📂 History", "⚙️ Settings"], label_visibility="collapsed")

        st.markdown("---")
        st.markdown("### System Status")
        ollama_status = check_ollama()
        if ollama_status:
            st.markdown('<div><span class="status-dot status-online"></span><b>Ollama Online</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div><span class="status-dot status-offline"></span><b>Ollama Offline</b></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.caption("v1.0.0 | Built with ❤️")

    # --- Main Content ---
    if page == "🚀 Scraper":
        st.title("🚀 AI Web Scraper")
        st.markdown("##### Turn any natural language prompt into clean, structured data.")

        if not ollama_status:
            st.error(f"⚠️ **Ollama Offline:** Unable to reach `{OLLAMA_HOST}`. Please ensure Ollama is running.")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        prompt = st.text_area(
            "What would you like to scrape today?",
            placeholder="e.g. Scrape the product name, price, and rating of the latest iPhone models from Amazon.",
            height=120,
            help="Describe the site and the fields you want to extract."
        )

        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            start_button = st.button("✨ Start Magic Scraping")
        st.markdown('</div>', unsafe_allow_html=True)

        if start_button:
            if prompt:
                with st.status("🛠️ Working on your request...", expanded=True) as status:
                    try:
                        orchestrator = ScraperOrchestrator()

                        st.write("🔍 Analyzing prompt with AI...")
                        # In a real app, we might add more granular feedback here
                        result = orchestrator.run(prompt)

                        if result:
                            status.update(label="✅ Scraping Complete!", state="complete", expanded=False)
                            st.balloons()

                            st.success(f"Successfully extracted **{len(result['records'])}** records.")

                            tabs = st.tabs(["📊 Data Explorer", "🧠 AI Insights", "📥 Download"])

                            with tabs[0]:
                                st.dataframe(pd.DataFrame(result['records']), use_container_width=True)

                            with tabs[1]:
                                st.subheader("Prompt Interpretation")
                                st.json(result['interpretation'])

                                if result['interpretation'].get('suggested_fields'):
                                    st.info(f"💡 **Tip:** You could also extract: {', '.join(result['interpretation']['suggested_fields'])}")

                            with tabs[2]:
                                c1, c2 = st.columns(2)
                                with c1:
                                    with open(result['json_path'], "rb") as f:
                                        st.download_button(
                                            label="📥 Download JSON",
                                            data=f,
                                            file_name=os.path.basename(result['json_path']),
                                            mime="application/json"
                                        )
                                with c2:
                                    with open(result['csv_path'], "rb") as f:
                                        st.download_button(
                                            label="📥 Download CSV",
                                            data=f,
                                            file_name=os.path.basename(result['csv_path']),
                                            mime="text/csv"
                                        )
                        else:
                            status.update(label="❌ No data found.", state="error")
                            st.warning("The scraper couldn't find any data matching your request.")
                    except Exception as e:
                        status.update(label="❌ An error occurred.", state="error")
                        st.error(f"Error details: {e}")
            else:
                st.warning("Please provide a prompt to start.")

    elif page == "📂 History":
        st.title("📂 Scraping History")
        st.markdown("Manage and review your previous scraping sessions.")

        files = list(OUTPUT_DIR.glob("*.json"))
        files.sort(key=os.path.getmtime, reverse=True)

        if not files:
            st.info("No saved sessions found. Start scraping to populate your history!")
        else:
            # Create a nice selection interface
            selected_file_name = st.selectbox("Select a previous session to view:", [f.name for f in files])

            if selected_file_name:
                selected_file = OUTPUT_DIR / selected_file_name
                with open(selected_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Summary Cards
                st.markdown('<div class="card">', unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Records", data['metadata'].get('total_records', 0))
                m2.metric("Fields", len(data['metadata'].get('fields_extracted', [])))
                m3.metric("Format", "JSON/CSV")
                m4.metric("Status", "Completed")

                st.write(f"**URL:** {data['metadata'].get('source_url')}")
                st.write(f"**Prompt:** {data['metadata'].get('user_prompt')}")
                st.markdown('</div>', unsafe_allow_html=True)

                st.subheader("Data Preview")
                st.dataframe(pd.DataFrame(data['records']), use_container_width=True)

                csv_file = selected_file.with_suffix('.csv')
                if csv_file.exists():
                    with open(csv_file, "rb") as f:
                        st.download_button("📂 Download CSV Again", f, file_name=csv_file.name)

    elif page == "⚙️ Settings":
        st.title("⚙️ System Settings")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🔑 API Credentials")
        col_a, col_b = st.columns(2)
        with col_a:
            s_api = st.text_input("ScraperAPI Key", value=SCRAPERAPI_KEY or "", type="password", help="Primary fetching API")
        with col_b:
            sb_api = st.text_input("ScrapingBee Key", value=SCRAPINGBEE_KEY or "", type="password", help="Fallback fetching API")

        st.markdown("---")

        st.subheader("🤖 Local LLM (Ollama)")
        col_c, col_d = st.columns(2)
        with col_c:
            model = st.selectbox("Default Model", ["llama3", "mistral", "phi3", "llama2"], index=0)
        with col_d:
            host = st.text_input("Ollama Endpoint", value=OLLAMA_HOST)

        if st.button("💾 Save Configuration"):
            with open(".env", "w") as f:
                f.write(f"SCRAPERAPI_KEY={s_api}\n")
                f.write(f"SCRAPINGBEE_KEY={sb_api}\n")
                f.write(f"OLLAMA_MODEL={model}\n")
                f.write(f"OLLAMA_HOST={host}\n")
                f.write(f"OUTPUT_DIR=outputs\n")
                f.write(f"LOG_DIR=logs\n")
            st.toast("Settings saved!", icon="✅")
            st.success("Configuration updated successfully.")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
