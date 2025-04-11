# CineAI-Agents 🎬🤖

**CineAI Agents** is an innovative project that combines artificial intelligence, decentralized storage, and audiovisual content analysis. It consists of two AI agents that work together to analyze and summarize movie and TV reviews from Filmaffinity, store the data in a decentralized manner in Storacha, and provide interactive responses in a Telegram bot.

<img src="assets/storacha-w3.jpeg" alt="storacha-w3" width="500" height="500"/>
---

## **Project Description**

The project consists of two AI agents:

1. **LangChain Agent (Web Scraper)**:
- Performs web scraping of movie and TV reviews from Filmaffinity.
- Analyzes and summarizes the reviews using language models like Ollama.
- Stores the reviews and analysis in Storacha, a decentralized storage system based on Filecoin.

2. **ElizaOS Agent (Telegram Bot)**:
- Is an interactive bot that joins Telegram groups.
- Answers questions about movies and TV shows based on comments stored in Storacha.
- Its personality and answers are trained using decentralized data.

3. Storacha
- We've integrated Storacha to decentrally store the FAISS index and comment data. This ensures that the information is securely and easily accessible on the Filecoin network.

---

## **Workflow**

1. **Web Scraping and Analysis**:
- The user provides a Filmaffinity URL.
- The LangChain Agent scrapes the comments.
- The comments are analyzed and summarized using a language model.
- The data is stored in Storacha.

2. **Interaction with the Bot**:
- The ElizaOS Agent (Telegram bot) joins a group.
- Users can ask questions about movies or TV shows.
- The bot responds by calculating the comments stored in Storacha.

3. **Decentralized Storage**:
- Storacha is used to store comments and analysis in a decentralized manner.
- This makes the data available for future reference and training.

---

## **Technologies Used**

- **LangChain**: For web scraping and comment analysis.
- **Ollama**: Language model for summarizing and analyzing comments.
- **Storacha**: Decentralized data storage.
- **ElizaOS**: For creating a Telegram bot with a trained personality.
- **Telegram Bot API**: For interacting with users in Telegram groups.
- **Streamlit**: Optional interface for testing the LangChain Agent.

---

## **Installation and Use**

### Requirements
- Python 3.8+
- Node.js (for the Storacha client)
- Telegram account for the bot.

### Steps to Run the Project
1. Clone the repository:
``` 
git clone https://github.com/your-username/CineAI-Agents.git
cd CineAI-Agents
```
2. Install Ollama:
- Download and install Ollama from its [official website](https://ollama.com/).
- Follow the installation instructions for your operating system.

3. Download the Stable LM 2 Model:

Once Ollama is installed, download the stablelm2 model (1.6B parameters) by running the following command in your terminal:
```bash
ollama pull stablelm2
```
This model is ideal for our project because it supports multiple languages ​​(English, Spanish, German, Italian, French, Portuguese, and Dutch), making it perfect for analyzing comments in different languages.

