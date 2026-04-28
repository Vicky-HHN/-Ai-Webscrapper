import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from core.scraper import ScraperOrchestrator
from config import OUTPUT_DIR, OLLAMA_MODEL, OLLAMA_HOST, SCRAPERAPI_KEY, SCRAPINGBEE_KEY
import requests

st.set_page_config(page_title="SmartScraper Dashboard", layout="wide")

def check_ollama():
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        return response.status_code == 200
    except:
        return False

def main():
    st.sidebar.title("SmartScraper")
    page = st.sidebar.radio("Navigate", ["Scraper", "History", "Settings"])

    if not check_ollama():
        st.error(f"⚠️ Ollama is not running at {OLLAMA_HOST}. Please start Ollama to use the LLM features.")

    if page == "Scraper":
        st.header("🚀 AI Web Scraper")
        prompt = st.text_area("What do you want to scrape?", placeholder="e.g. Scrape the product name, price, and rating of laptops from Amazon.")

        if st.button("Start Scraping"):
            if prompt:
                with st.spinner("Processing prompt and scraping..."):
                    try:
                        orchestrator = ScraperOrchestrator()
                        result = orchestrator.run(prompt)
                        if result:
                            st.success(f"Successfully scraped {len(result['records'])} records!")
                            st.subheader("Preview")
                            st.dataframe(pd.DataFrame(result['records']))

                            col1, col2 = st.columns(2)
                            with col1:
                                with open(result['json_path'], "rb") as f:
                                    st.download_button("Download JSON", f, file_name=os.path.basename(result['json_path']))
                            with col2:
                                with open(result['csv_path'], "rb") as f:
                                    st.download_button("Download CSV", f, file_name=os.path.basename(result['csv_path']))
                        else:
                            st.warning("No data found.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please enter a prompt.")

    elif page == "History":
        st.header("📂 Scraping History")
        files = list(OUTPUT_DIR.glob("*.json"))
        files.sort(key=os.path.getmtime, reverse=True)

        if not files:
            st.info("No history found.")
        else:
            selected_file = st.selectbox("Select a past scrape session", [f.name for f in files])
            if selected_file:
                with open(OUTPUT_DIR / selected_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    st.subheader("Session Metadata")
                    st.json(data['metadata'])
                    st.subheader("Scraped Records")
                    st.dataframe(pd.DataFrame(data['records']))

    elif page == "Settings":
        st.header("⚙️ Settings")
        st.subheader("API Keys")
        s_api = st.text_input("ScraperAPI Key", value=SCRAPERAPI_KEY or "", type="password")
        sb_api = st.text_input("ScrapingBee Key", value=SCRAPINGBEE_KEY or "", type="password")

        st.subheader("LLM Configuration")
        model = st.selectbox("Ollama Model", ["llama3", "mistral", "phi3"], index=0)
        host = st.text_input("Ollama Host", value=OLLAMA_HOST)

        if st.button("Save Settings"):
            # Update .env file
            with open(".env", "w") as f:
                f.write(f"SCRAPERAPI_KEY={s_api}\n")
                f.write(f"SCRAPINGBEE_KEY={sb_api}\n")
                f.write(f"OLLAMA_MODEL={model}\n")
                f.write(f"OLLAMA_HOST={host}\n")
                f.write(f"OUTPUT_DIR=outputs\n")
                f.write(f"LOG_DIR=logs\n")
            st.success("Settings saved! Please restart the app for changes to take effect.")

if __name__ == "__main__":
    main()
