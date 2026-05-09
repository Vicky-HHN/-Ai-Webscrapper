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

    /* Container Styling (replacing custom cards) */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: white;
        border-radius: 15px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
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

def init_session_state():
    if "config" not in st.session_state:
        st.session_state.config = {
            "scraperapi_key": SCRAPERAPI_KEY or "",
            "scrapingbee_key": SCRAPINGBEE_KEY or "",
            "ollama_model": OLLAMA_MODEL or "llama3",
            "ollama_host": OLLAMA_HOST or "http://localhost:11434"
        }

def main():
    init_session_state()

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
            with st.container(border=True):
                st.error(f"⚠️ **Ollama Offline:** Unable to reach `{st.session_state.config['ollama_host']}`")
                st.info("""
                    **How to fix:**
                    1. Ensure [Ollama](https://ollama.com/) is installed and running on your machine.
                    2. Pull the required model by running: `ollama pull llama3` (or your selected model).
                    3. If you are using a custom endpoint, check it in the **Settings** tab.
                """)

        with st.container(border=True):
            prompt = st.text_area(
                "What would you like to scrape today?",
                placeholder="e.g. Scrape the product name, price, and rating of the latest iPhone models from Amazon.",
                height=120,
                help="Describe the site and the fields you want to extract."
            )

            col1, col2, col3 = st.columns([1, 1.5, 1])
            with col2:
                start_button = st.button("✨ Start Magic Scraping")

        if start_button:
            if prompt:
                with st.status("🛠️ Working on your request...", expanded=True) as status:
                    try:
                        # Use session state for dynamic config
                        orchestrator = ScraperOrchestrator()
                        # Override orchestrator config from session state
                        orchestrator.llm.model = st.session_state.config['ollama_model']
                        orchestrator.llm.client.base_url = st.session_state.config['ollama_host']
                        orchestrator.fetcher.scraperapi_key = st.session_state.config['scraperapi_key']
                        orchestrator.fetcher.scrapingbee_key = st.session_state.config['scrapingbee_key']

                        # We can also pass a callback that uses st.empty to update a single line
                        # but st.write inside st.status works well for a list of steps.
                        result = orchestrator.run(prompt, status_callback=st.write)

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
                        error_msg = str(e)
                        if "connection" in error_msg.lower() or "11434" in error_msg:
                            st.error("🔌 **Connection Error:** Could not reach the Ollama server. Is it running?")
                        elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                            st.error(f"🧠 **Model Missing:** The model `{st.session_state.config['ollama_model']}` was not found. Try running `ollama pull {st.session_state.config['ollama_model']}`.")
                        else:
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
                with st.container(border=True):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Records", data['metadata'].get('total_records', 0))
                    m2.metric("Fields", len(data['metadata'].get('fields_extracted', [])))
                    m3.metric("Format", "JSON/CSV")
                    m4.metric("Status", "Completed")

                    st.write(f"**URL:** {data['metadata'].get('source_url')}")
                    st.write(f"**Prompt:** {data['metadata'].get('user_prompt')}")

                st.subheader("Data Preview")
                st.dataframe(pd.DataFrame(data['records']), use_container_width=True)

                csv_file = selected_file.with_suffix('.csv')
                if csv_file.exists():
                    with open(csv_file, "rb") as f:
                        st.download_button("📂 Download CSV Again", f, file_name=csv_file.name)

    elif page == "⚙️ Settings":
        st.title("⚙️ System Settings")

        with st.container(border=True):
            st.subheader("🔑 API Credentials")
            st.markdown("""
            Need keys? Get them here:
            [ScraperAPI](https://www.scraperapi.com/) (Primary) |
            [ScrapingBee](https://www.scrapingbee.com/) (Fallback)
            """)

            col_a, col_b = st.columns(2, gap="large")
            with col_a:
                s_api = st.text_input(
                    "ScraperAPI Key",
                    value=st.session_state.config['scraperapi_key'],
                    type="password",
                    placeholder="sapi-..."
                )
                if s_api:
                    st.markdown("<span style='color: #4CAF50; font-size: 0.8rem;'>● Key provided</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color: #FF4B4B; font-size: 0.8rem;'>● Key missing</span>", unsafe_allow_html=True)

            with col_b:
                sb_api = st.text_input(
                    "ScrapingBee Key",
                    value=st.session_state.config['scrapingbee_key'],
                    type="password",
                    placeholder="spb-..."
                )
                if sb_api:
                    st.markdown("<span style='color: #4CAF50; font-size: 0.8rem;'>● Key provided</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color: #FF4B4B; font-size: 0.8rem;'>● Key missing</span>", unsafe_allow_html=True)

            st.markdown("---")

            st.subheader("🤖 Local LLM (Ollama)")
            col_c, col_d = st.columns(2, gap="large")
            with col_c:
                current_model = st.session_state.config['ollama_model']
                model_options = ["llama3", "mistral", "phi3", "llama2"]
                model_idx = model_options.index(current_model) if current_model in model_options else 0
                model = st.selectbox("Default Model", model_options, index=model_idx)
            with col_d:
                host = st.text_input("Ollama Endpoint", value=st.session_state.config['ollama_host'])

            if st.button("💾 Save Configuration"):
                # Update session state
                st.session_state.config.update({
                    "scraperapi_key": s_api,
                    "scrapingbee_key": sb_api,
                    "ollama_model": model,
                    "ollama_host": host
                })

                # Persist to .env
                with open(".env", "w") as f:
                    f.write(f"SCRAPERAPI_KEY={s_api}\n")
                    f.write(f"SCRAPINGBEE_KEY={sb_api}\n")
                    f.write(f"OLLAMA_MODEL={model}\n")
                    f.write(f"OLLAMA_HOST={host}\n")
                    f.write(f"OUTPUT_DIR=outputs\n")
                    f.write(f"LOG_DIR=logs\n")
                st.toast("Settings saved!", icon="✅")
                st.success("Configuration updated successfully.")

if __name__ == "__main__":
    main()
