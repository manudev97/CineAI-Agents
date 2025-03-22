import requests
from bs4 import BeautifulSoup
import streamlit as st
from langchain_ollama import OllamaLLM
import python_filmaffinity

# Initialize FilmAffinity
fa = python_filmaffinity.FilmAffinity()

# Load AI Model
llm = OllamaLLM(model="stablelm2")  # Change to "mistral" or another model if necessary

# Function to scrape the comments of a movie
def scrape_reviews(url):
    try:
        st.write(f'\n 🗃️ Scraping website: {url}')
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return f"⚠️ Failed to fetch {url}"

        # Extract the comments
        soup = BeautifulSoup(response.text, "html.parser")
        reviews = soup.find_all("td", class_="rev-text")

        if not reviews:
            return "❌ No reviews found on this page."

        # Extract the text of each comment
        text = " ".join([review.a.get_text(strip=True) for review in reviews if review.a])

        return text[:2000]  # Limit characters to avoid overloading the AI
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Function to summarize content using AI
def summarize_content(content):
    st.write("✍️ Summarizing content...")
    return llm.invoke(f"Summarize the following content:\n\n{content[:1000]}")  # Limit to 1000 characters

# UI Streamlit
st.title("🤖 CineAI-Agents - Web Scraper")
st.write("💫 Enter a movie title below and get a summary of the reviews!")

# User input for the audiovisual title
movie_title = st.text_input("🎬 Enter Title of the Audiovisual:")

if movie_title:
    # Search for movies related to the title
    peliculas = fa.search(title=movie_title)

    if not peliculas:
        st.write("❌ No movies found with that title.")
    else:
        # Show found movies with a checkbox
        st.write("📋 Select the audiovisual you are interested in:")
        selected_movie = None

        for i, pelicula in enumerate(peliculas):
            # Create a checkbox for each movie
            if st.checkbox(f"[{pelicula['year']}] {' '.join(dict.fromkeys(pelicula['title'].split('\n')))} | {pelicula['country']} | ID: {pelicula['id']}", key=f"movie_{i}"):
                selected_movie = pelicula

        # Button to summarize the comments of the selected movie
        if selected_movie and st.button("📄 Summarize Reviews"):
            # Build the Filmaffinity URL for the selected movie
            movie_url = f"https://www.filmaffinity.com/es/pro-reviews.php?movie-id={selected_movie['id']}"

            # Get movie reviews
            content = scrape_reviews(movie_url)

            if "⚠️ Failed" in content or "❌ Error" in content or "❌ No reviews" in content:
                st.write(content)
            else:
                # Summarize the comments
                summary = summarize_content(content)
                st.subheader(f"📄 Reviews Summary for {' '.join(dict.fromkeys(selected_movie['title'].split('\n')))}")
                st.write(summary)