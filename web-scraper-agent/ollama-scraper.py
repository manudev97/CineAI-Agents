import requests 
from bs4 import BeautifulSoup
import streamlit as st
from langchain_ollama import OllamaLLM

# Load AI Model
llm = OllamaLLM(model="stablelm2") # Change to "mistral" or another model

# Scrape a website
def scraper_website(url):
    try:
        st.write(f'\n 🗃️ Scraping website: {url}')
        headers = {"User-Agent": "Mozila/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return f"⚠️ Failed to fetch {url}"
        
        # Extract review content
        soup = BeautifulSoup(response.text, "html.parser")
        reviews = soup.find_all("div", itemprop="reviewBody")  # Look for the comments

        if not reviews:
            return "❌ No reviews found on this page."

        # Extract the text of each comment
        text = " ".join([review.get_text(strip=True) for review in reviews])

        return text[:2000] # Limit characters to avoid overloading AI
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Function to summarize content using AI
def summarize_content(content):
    st.write("✍️ Summarizing content...")
    return llm.invoke(f"Summarize the follwing content:\n\n{content[:1000]}") # Limit to 1000 chars

# Streamlit Web UI
st.title("🤖 CineAI-Agents - Web Scraper")
st.write("💫 Enter a website URL below and get a summarized version!") 

# User input 
url = st.text_input("🔗 Enter Website URL:")
if url:
    content = scraper_website(url)

    if "⚠️ Failed" in content or "❌ Error" in content:
        st.write(content)
    else:
        summary = summarize_content(content)
        st.subheader("📄 Website Summary")
        st.write(summary)