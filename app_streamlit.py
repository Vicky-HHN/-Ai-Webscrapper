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

# --- Custom Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        border: none;
    }
    .stTextArea>div>div>textarea {
        border-radius: 10px;
    }
    .sidebar .sidebar-content {
        background-image: linear-gradient(#2e7bcf,#2e7bcf);
        color: white;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
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
        st.title("🕸️ SmartScraper AI")
        st.markdown("---")
        page = st.radio("Navigate", ["🚀 Scraper", "📂 History", "⚙️ Settings"])

        st.markdown("---")
        st.markdown("### Status")
        ollama_status = check_ollama()
        if ollama_status:
            st.success("● Ollama Online")
        else:
            st.error("○ Ollama Offline")

        st.info("Built with 💙 using Python & Ollama")

    # --- Main Content ---
    if page == "🚀 Scraper":
        st.title("🚀 AI-Powered Web Scraper")
        st.markdown("Transform natural language into structured data instantly.")

        if not ollama_status:
            st.warning(f"⚠️ Ollama is not detected at `{OLLAMA_HOST}`. Scraper interpretation will fail. Please start Ollama and pull `{OLLAMA_MODEL}`.")

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            prompt = st.text_area(
                "Describe what you want to scrape:",
                placeholder="e.g. Scrape the product name, price, and rating of the latest MacBook Pro models from Amazon.",
                height=150
            )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                start_button = st.button("Start AI Scraping")
            st.markdown('</div>', unsafe_allow_html=True)

        if start_button:
            if prompt:
                status_container = st.empty()
                progress_bar = st.progress(0)

                try:
                    orchestrator = ScraperOrchestrator()

                    status_container.info("🧠 AI is interpreting your prompt...")
                    progress_bar.progress(25)

                    # We'll need to capture the prints or modify orchestrator for better feedback
                    # For now, just run it
                    result = orchestrator.run(prompt)

                    progress_bar.progress(100)

                    if result:
                        st.balloons()
                        st.success(f"Successfully scraped {len(result['records'])} records!")

                        # Results display
                        tabs = st.tabs(["📊 Data Preview", "📝 Prompt Interpretation", "💾 Export"])

                        with tabs[0]:
                            st.dataframe(pd.DataFrame(result['records']), use_container_width=True)

                        with tabs[1]:
                            st.json(result['interpretation'])

                        with tabs[2]:
                            c1, c2 = st.columns(2)
                            with c1:
                                with open(result['json_path'], "rb") as f:
                                    st.download_button(
                                        label="Download JSON",
                                        data=f,
                                        file_name=os.path.basename(result['json_path']),
                                        mime="application/json"
                                    )
                            with c2:
                                with open(result['csv_path'], "rb") as f:
                                    st.download_button(
                                        label="Download CSV",
                                        data=f,
                                        file_name=os.path.basename(result['csv_path']),
                                        mime="text/csv"
                                    )
                    else:
                        st.warning("No data found or validation failed.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("Please enter a prompt to begin.")

    elif page == "📂 History":
        st.title("📂 Scraping History")
        st.markdown("View and download your past scraping sessions.")

        files = list(OUTPUT_DIR.glob("*.json"))
        files.sort(key=os.path.getmtime, reverse=True)

        if not files:
            st.info("No history found yet. Start scraping to see your results here!")
        else:
            selected_file_name = st.selectbox("Select a past session:", [f.name for f in files])

            if selected_file_name:
                selected_file = OUTPUT_DIR / selected_file_name
                with open(selected_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Statistics
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Records", data['metadata'].get('total_records', 0))
                m2.metric("Date", data['metadata'].get('scraped_at', 'N/A'))
                m3.metric("Fields", len(data['metadata'].get('fields_extracted', [])))

                with st.expander("Session Details", expanded=True):
                    st.write(f"**Source URL:** {data['metadata'].get('source_url')}")
                    st.write(f"**User Prompt:** {data['metadata'].get('user_prompt')}")

                st.subheader("Data Table")
                st.dataframe(pd.DataFrame(data['records']), use_container_width=True)

                # Download again from history
                csv_file = selected_file.with_suffix('.csv')
                if csv_file.exists():
                    with open(csv_file, "rb") as f:
                        st.download_button("Download CSV again", f, file_name=csv_file.name)

    elif page == "⚙️ Settings":
        st.title("⚙️ System Settings")

        tab1, tab2 = st.tabs(["🔑 API Keys", "🤖 LLM Config"])

        with tab1:
            st.subheader("External Scraping APIs")
            st.info("Keys are used to bypass CAPTCHAs and render JavaScript.")
            s_api = st.text_input("ScraperAPI Key", value=SCRAPERAPI_KEY or "", type="password")
            sb_api = st.text_input("ScrapingBee Key", value=SCRAPINGBEE_KEY or "", type="password")

        with tab2:
            st.subheader("Local LLM Configuration")
            model = st.selectbox("Ollama Model", ["llama3", "mistral", "phi3", "llama2"], index=0)
            host = st.text_input("Ollama Host URL", value=OLLAMA_HOST)

        if st.button("💾 Save All Settings"):
            with open(".env", "w") as f:
                f.write(f"SCRAPERAPI_KEY={s_api}\n")
                f.write(f"SCRAPINGBEE_KEY={sb_api}\n")
                f.write(f"OLLAMA_MODEL={model}\n")
                f.write(f"OLLAMA_HOST={host}\n")
                f.write(f"OUTPUT_DIR=outputs\n")
                f.write(f"LOG_DIR=logs\n")
            st.success("✅ Settings saved successfully! Refresh the page to apply.")

if __name__ == "__main__":
    main()
