# 🇮🇳 Political Multi-Agent Hybrid RAG

### An Agentic RAG System for Exploring and Comparing Indian Political Manifestos

A multi-agent AI chatbot for querying, researching, and comparing Indian political party manifestos across different parties and election years.

The system combines **Multi-Agent AI, Hybrid RAG, Multi-Query Retrieval, BM25, ChromaDB, RRF, Cross-Encoder Reranking, LangGraph, and Groq LLMs**.

---

## 📸 Application Preview

<p align="center">
  <img src="assets/screenshot1.png" width="48%">
  <img src="assets/screenshot2.png" width="48%">
</p>

---

## 🚀 Features

* 🤖 Multi-Agent architecture using LangGraph
* 🔎 Hybrid RAG with semantic + keyword retrieval
* 🧠 Multi-Query Retrieval
* 🔤 BM25 keyword search
* 📚 ChromaDB vector database
* 🔄 Reciprocal Rank Fusion (RRF)
* 🎯 Cross-Encoder reranking
* ⚖️ Political manifesto comparison
* 💬 Conversational follow-up questions
* 💾 SQLite conversation memory
* 🎨 Streamlit interface
* 📊 LangSmith observability

---

## 🧠 Architecture

```text
                         User Query
                              │
                              ▼
                     ┌─────────────────┐
                     │   Task Agent    │
                     │  Query Routing  │
                     └────────┬────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
         Casual           Research        Comparison
          Agent             Agent            Agent
                              │
                              ▼
                     Multi-Query Retrieval
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              ChromaDB                BM25
            Semantic Search       Keyword Search
                    │                   │
                    └─────────┬─────────┘
                              ▼
                             RRF
                              │
                              ▼
                    Cross-Encoder Reranking
                              │
                              ▼
                       Relevant Evidence
                              │
                              ▼
                          Groq LLM
                              │
                              ▼
                        Final Answer
```

---

## 🔎 RAG Pipeline

```text
User Query
    ↓
Query Generation
    ↓
Multiple Queries
    ↓
 ┌───────────┬───────────┐
 ↓           ↓
ChromaDB    BM25
 ↓           ↓
 └─────→ RRF ←─────┘
          ↓
Cross-Encoder
          ↓
Relevant Documents
          ↓
       Groq LLM
          ↓
    Final Answer
```

### Retrieval Components

| Component     | Purpose                     |
| ------------- | --------------------------- |
| ChromaDB      | Semantic retrieval          |
| BM25          | Keyword retrieval           |
| Multi-Query   | Improves search coverage    |
| RRF           | Combines retrieval results  |
| Cross-Encoder | Reranks retrieved documents |

---

## 🗄️ Knowledge Base

The knowledge base contains political manifesto documents from parties including:

* Bharatiya Janata Party (BJP)
* Indian National Congress
* All India Trinamool Congress (TMC)
* Communist Party of India (Marxist)

The system supports manifesto documents from multiple election years.

---

## 💬 Example Queries

```text
What does BJP say about unemployment?

What does Congress say about employment?

Compare BJP and Congress on unemployment.

What is the main issue raised by TMC in its manifesto?

What about Congress?
```

The chatbot maintains conversation context for follow-up questions.

---

## 🛠️ Tech Stack

**Languages**

* Python

**Generative AI**

* Groq
* Llama 3.3 70B

**AI Frameworks**

* LangChain
* LangGraph

**RAG / Retrieval**

* ChromaDB
* Sentence Transformers
* BM25
* Reciprocal Rank Fusion
* Cross-Encoder Reranking

**Frontend**

* Streamlit

**Database / Memory**

* SQLite

**Observability**

* LangSmith

---

## 📁 Project Structure

```text
Political-MultiAgent-Hybrid-RAG/
│
├── assets/
│   ├── political_background.png
│   ├── screenshot1.png
│   └── screenshot2.png
│
├── code/
│   ├── agents.py
│   ├── app.py
│   ├── chatbot.py
│   ├── check_setup.py
│   ├── config.py
│   ├── data_processing.py
│   ├── rag.py
│   └── read_pdfs.py
│
├── database/
│   └── chroma_db/
│
├── documents/
│   ├── Manifesto PDFs
│   └── Extracted text files
│
├── .gitignore
├── .python-version
├── README.md
├── project_notes.md
├── pyproject.toml
└── requirements.txt
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Political-MultiAgent-Hybrid-RAG.git
cd Political-MultiAgent-Hybrid-RAG
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Environment

**Windows:**

```powershell
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=political-gpt
```

---

## ▶️ Run the Application

```bash
streamlit run code/app.py
```

---

## 🚧 Future Improvements

* Add more political parties and manifesto years
* Add page-level source citations
* Add multilingual manifesto support
* Improve RAG evaluation
* Improve fact-checking
* Add structured policy comparison tables

---

## ⚠️ Disclaimer

This project is an **AI-based research and exploration tool**.

Responses are generated from the manifesto documents available in the system and should not be considered political advice or independent verification of political claims.

Users should refer to the original manifesto documents for authoritative information.

---

## 👨‍💻 Author

**Dhruv Kumar**

Built with:

**Generative AI • Agentic AI • RAG • Information Retrieval • Political Document Analysis**
