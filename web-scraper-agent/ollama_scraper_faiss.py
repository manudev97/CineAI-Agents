import requests, os
import streamlit as st
import python_filmaffinity
import faiss
import numpy as np
from bs4 import BeautifulSoup
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
import subprocess
from datetime import datetime
import uuid
from storacha_utils import StorachaClient

# Inicialización del cliente
storacha = StorachaClient()

# Initialize FilmAffinity
fa = python_filmaffinity.FilmAffinity()

# Load AI Model
llm = OllamaLLM(model="stablelm2")  # Change to "mistral" or another model if necessary

# Load HuggingFace Embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load FAISS Vector Store
index = faiss.IndexFlatL2(384) # Vector dimension for MiniLM
vector_store = {}

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

        return text[:5000]  # Limit characters to avoid overloading the AI
    except Exception as e:
        return f"❌ Error: {str(e)}"
    
# Function to store data in FAISS
def store_in_faiss(text, url):
    global index, vector_store
    st.write("📦 Storing data in FAISS...")

    # Split text into chunks
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    texts = splitter.split_text(text)

    # Embed each chunk
    vectors = embeddings.embed_documents(texts)
    vectors = np.array(vectors, dtype=np.float32)

    # Store in FAISS
    index.add(vectors)
    save_faiss_index(index)
    vector_store[len(vector_store)] = (url, text)

    return "✅ Data stored in FAISS."

# Function to retrieve relevant chunks and answer questions
def retrieve_and_answer(query):
    global index, vector_store

    # Convert query into embedding
    query_vector = np.array(embeddings.embed_query(query), dtype=np.float32).reshape(1, -1)

    # Search FAISS for similar vectors
    D, I = index.search(query_vector, k=2) # Return 2 most similar vectors

    context = ""
    for idx in I[0]:
        if idx in vector_store:
            context += " ".join(vector_store[idx][1]) + "\n\n"

    if not context:
        return "🤖 No relevant information found."
    
    #Ask AI to generate an answer
    return llm.invoke(f"Based on the following context, answer the question:\n\n{context}\n\nQuestion: {query}\nAnswer:")

# Function to summarize content using AI
def summarize_and_upload(content, movie_id, movie_title):
    """Función combinada que resume y sube a Storacha"""
    with st.spinner("✍️ Generando resumen..."):
        summary = llm.invoke(f"Summarize the following content:\n\n{content[:1000]}")
    
    st.subheader(f"📄 Reviews Summary for {' '.join(dict.fromkeys(movie_title.split('\n')))}")
    st.write(summary)
    
    # Automatic upload to Storacha
    with st.spinner("☁️ Subiendo a Storacha..."):
        # Configure if it is the first time
        if not storacha.ready:
            if not storacha.setup():
                st.error("Error configurando Storacha")
                return summary
        
        # Upload the summary
        result = storacha.upload_text(summary, movie_title)
        
        if result["status"] == "success":
            st.success("✅ Review uploaded successfully!")
            st.code(f"CID: {result['cid']}", language="text")
            st.markdown(f"🔗 [Ver en IPFS Gateway](https://{result['cid']}.ipfs.w3s.link)")
        else:
            st.error(f"❌ Error: {result['message']}")
    
    return summary

# Function to save FAISS index to a file
def save_faiss_index(index, filename="faiss_index.idx"):
    faiss.write_index(index, filename)
    return filename

# # Function to upload FAISS index to Storacha
# def upload_to_storacha(filename):
#     # Use Storacha CLI or API to upload the file
#     os.system(f"storacha upload {filename}")
#     return f"✅ {filename} uploaded to Storacha."

# # Function to download FAISS index from Storacha
# def download_from_storacha(filename):
#     # Use Storacha CLI or API to download the file
#     os.system(f"storacha download {filename}")
#     return f"✅ {filename} downloaded from Storacha."

# # Function to load FAISS index from a file
# def load_faiss_index(filename="faiss_index.idx"):
#     return faiss.read_index(filename)

    

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
                # Combined process: summarize + upload to Storacha
                summary = summarize_and_upload(
                    content,
                    selected_movie['id'],
                    selected_movie['title']
                )
                
                # Store in FAISS
                store_message = store_in_faiss(content, movie_url)
                st.write(store_message)


            # # Storacha
            # # Example usage
            # if st.button("💾 Save FAISS Index to Storacha"):
            #     filename = save_faiss_index(index)
            #     upload_message = upload_to_storacha(filename)
            #     st.write(upload_message)

            # if st.button("📥 Load FAISS Index from Storacha"):
            #     download_message = download_from_storacha("faiss_index.idx")
            #     index = load_faiss_index()
            #     st.write(download_message)



# Ask a question
st.write("🤔 Ask a question about the reviews:")
query = st.text_input("❓ Enter your question:")
if query:
    answer = retrieve_and_answer(query)
    st.write(answer)

