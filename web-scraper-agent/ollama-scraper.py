import requests
from bs4 import BeautifulSoup
import streamlit as st
from langchain_ollama import OllamaLLM
import python_filmaffinity

# Inicializar FilmAffinity
fa = python_filmaffinity.FilmAffinity()

# Load AI Model
llm = OllamaLLM(model="stablelm2")  # Cambia a "mistral" u otro modelo si es necesario

# Función para scrapear los comentarios de una película
def scrape_reviews(url):
    try:
        st.write(f'\n 🗃️ Scraping website: {url}')
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return f"⚠️ Failed to fetch {url}"

        # Extraer los comentarios
        soup = BeautifulSoup(response.text, "html.parser")
        reviews = soup.find_all("div", itemprop="reviewBody")

        if not reviews:
            return "❌ No reviews found on this page."

        # Extraer el texto de cada comentario
        text = " ".join([review.get_text(strip=True) for review in reviews])

        return text[:2000]  # Limitar caracteres para evitar sobrecargar la IA
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Función para resumir el contenido usando IA
def summarize_content(content):
    st.write("✍️ Summarizing content...")
    return llm.invoke(f"Summarize the following content:\n\n{content[:1000]}")  # Limitar a 1000 caracteres

# Interfaz de Streamlit
st.title("🤖 CineAI-Agents - Web Scraper")
st.write("💫 Enter a movie title below and get a summary of the reviews!")

# Input del usuario para el título de la película
movie_title = st.text_input("🎬 Enter Title of the Audiovisual:")

if movie_title:
    # Buscar películas relacionadas con el título
    peliculas = fa.search(title=movie_title)

    if not peliculas:
        st.write("❌ No movies found with that title.")
    else:
        # Mostrar las películas encontradas con un checkbox
        st.write("📋 Select the audiovisual you are interested in:")
        selected_movie = None

        for i, pelicula in enumerate(peliculas):
            # Crear un checkbox para cada película
            if st.checkbox(f"[{pelicula['year']}] {' '.join(dict.fromkeys(pelicula['title'].split('\n')))} | {pelicula['country']} | ID: {pelicula['id']}", key=f"movie_{i}"):
                selected_movie = pelicula

        # Botón para resumir los comentarios de la película seleccionada
        if selected_movie and st.button("📄 Summarize Reviews"):
            # Construir la URL de Filmaffinity para la película seleccionada
            movie_url = f"https://m.filmaffinity.com/es/film{selected_movie['id']}.html"

            # Obtener los comentarios de la película
            content = scrape_reviews(movie_url)

            if "⚠️ Failed" in content or "❌ Error" in content or "❌ No reviews" in content:
                st.write(content)
            else:
                # Resumir los comentarios
                summary = summarize_content(content)
                st.subheader(f"📄 Reviews Summary for {' '.join(dict.fromkeys(selected_movie['title'].split('\n')))}")
                st.write(summary)