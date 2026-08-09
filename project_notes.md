# Political RAG Chatbot - Project Notes

## Project Idea

The goal of this project is to build a multi-agent RAG chatbot
that can answer questions about political party manifestos and
other political documents.

The system will support multiple political parties and will be
able to research information and compare parties using evidence
from the uploaded documents.

## Initial Technology Stack

- Python
- LangChain
- LangGraph
- Groq
- ChromaDB
- Sentence Transformers
- BM25
- Docling
- LangSmith
- SQLite
- Streamlit

## Project Structure

The project is intentionally kept simple instead of separating
every component into multiple folders and files.

Main components:

- data_processing.py → document processing
- rag.py → retrieval pipeline
- agents.py → multi-agent logic
- chatbot.py → LangGraph workflow
- config.py → project configuration
- app.py → Streamlit interface

## Step 1 - Project Setup

### What I did

- Created the project structure.
- Set up the Python environment using uv.
- Added the initial dependencies.
- Configured Groq and LangSmith environment variables.
- Added configuration management using python-dotenv.

### Why

I want to build the project incrementally. The RAG pipeline will
be developed first, followed by the multi-agent LangGraph workflow,
persistence, observability, and finally deployment.

### Current Status

Project environment setup completed.

## Step 2 - PDF Text Extraction

### Approach

I decided to use PyMuPDF instead of a more complex document
processing framework.

The PDFs are processed page by page and the extracted text is
stored in text files.

### Why PyMuPDF?

- Simple to use
- Fast PDF text extraction
- Easy to process multiple PDFs
- Page numbers are preserved
- Suitable for the current project requirements

### Extraction Flow

PDF
→ PyMuPDF
→ Page-wise text extraction
→ Page markers
→ TXT file

### Important Design Decision

Page numbers are preserved during extraction because they will
later be used for source citations in the chatbot.

### Current Status

PDF text extraction implemented.
## Step 3 - Chunking and Metadata

### What I did

After extracting the PDF text page by page, I split the
documents into smaller chunks using RecursiveCharacterTextSplitter.

I used:

- Chunk size: 800
- Chunk overlap: 150

Each chunk also keeps metadata about the original document.

### Metadata

Each chunk stores:

- Party
- Year
- Document type
- Document name
- Page number

### Why metadata?

Metadata will allow the retrieval system to filter documents
based on party, election year and document type.

It will also allow the chatbot to provide page-level citations.

### Example

{
    "party": "BJP",
    "year": 2024,
    "document_type": "Lok Sabha Manifesto",
    "document": "Modi-Ki-Guarantee-Sankalp-Patra-English_2",
    "page": 42
}

### Current Flow

PDF
→ PyMuPDF
→ Page-wise TXT
→ Chunking
→ Metadata
→ Embedding

### Current Status

Chunking and metadata preparation implemented.

## Step 4 - Embeddings and ChromaDB

### What I did

After creating the document chunks, I generated vector
embeddings using the Sentence Transformers model:

all-MiniLM-L6-v2

The embeddings, original text and document metadata are stored
in a persistent ChromaDB collection.

### Why Sentence Transformers?

I wanted a lightweight embedding model that can run locally
without depending on an external embedding API.

### Why ChromaDB?

ChromaDB provides a simple persistent vector store for the
project and allows semantic similarity search over the
political document chunks.

### Stored Information

Each ChromaDB record contains:

- Chunk text
- Embedding vector
- Party
- Election year
- Document type
- Document name
- Page number
- Chunk number

### Ingestion Pipeline

PDF
→ PyMuPDF
→ Page-wise text
→ Chunking
→ Metadata
→ Sentence Transformer
→ Embeddings
→ ChromaDB

### Design Decision

I kept document ingestion and embedding/storage together in
data_processing.py because these steps form the offline
knowledge-base creation pipeline.

The retrieval logic will be implemented separately in rag.py.

### Current Status

2,231 chunks prepared and ready to be stored in ChromaDB.

## Step 4 - Embeddings and ChromaDB Result

The document ingestion pipeline successfully generated
embeddings for 2,231 chunks using the Sentence Transformers
model `all-MiniLM-L6-v2`.

The embeddings, text and metadata were stored in a persistent
ChromaDB collection.

### Result

Total chunks stored: 2,231

### Current Architecture

PDF
→ PyMuPDF
→ Page-wise text
→ Chunking
→ Metadata
→ Sentence Transformers
→ Embeddings
→ ChromaDB

## Step 5 - Basic Retrieval

The next stage is to build the retrieval layer separately
from the document ingestion process.

`rag.py` will only be responsible for retrieving relevant
information from the existing ChromaDB knowledge base.

I will first test basic semantic retrieval before adding
advanced techniques such as Multi-Query Retrieval, BM25 and
reranking.

### Current Retrieval Flow

User Query
→ Query Embedding
→ ChromaDB
→ Top-K Relevant Chunks

## Step 5 - Metadata-Aware Retrieval

### Problem

Basic semantic retrieval worked reasonably well, but it could
retrieve semantically related content from the wrong political
party.

For example, a query about Congress employment policies returned
a Communist Party employment-related chunk.

### Solution

I added metadata filtering to the ChromaDB retrieval layer.

The retrieval function can now optionally filter by:

- Party
- Year

### Example

A query such as:

"What does Congress say about employment?"

can be searched with:

party = Congress

A query such as:

"What did Congress propose about employment in 2024?"

can use:

party = Congress
year = 2024

### Updated Retrieval Flow

User Query
→ Metadata Filter
→ Semantic Search
→ Top-K Results

### Observation

Metadata filtering reduces cross-party retrieval noise while
keeping semantic similarity search.

### Next Step

Implement Multi-Query Retrieval (MQR) to improve retrieval for
complex or differently phrased questions.

## Step 7 - Hybrid Retrieval

### Problem

Semantic retrieval is good at understanding the meaning of a
query, but it can sometimes miss exact keywords, acronyms or
phrases.

### Solution

I added BM25 keyword retrieval alongside ChromaDB semantic
retrieval.

### Two Retrieval Methods

Semantic Retrieval:

Query
→ Sentence Transformer
→ ChromaDB
→ Similar documents

Keyword Retrieval:

Query
→ BM25
→ Keyword-based results

### Result Combination

The results from both retrieval methods are combined using
Reciprocal Rank Fusion (RRF).

RRF gives higher importance to documents that appear near the
top of multiple retrieval methods.

### Current Retrieval Architecture

User Query
→ Multi-Query Generation
→ Semantic Retrieval + BM25
→ Reciprocal Rank Fusion
→ Final Candidate Documents

Metadata filters for party and year are applied during
retrieval.

### Why Hybrid Retrieval?

Semantic retrieval captures meaning while BM25 helps with
exact terms and phrases. Combining both can improve retrieval
quality for political documents.

### Current Status

Multi-query hybrid retrieval implemented.

## Step 8 - Cross-Encoder Reranking

### Problem

The hybrid retrieval stage produces a candidate set, but the
ranking is based on retrieval signals rather than directly
evaluating the relationship between the user question and each
chunk.

### Solution

I added a Cross-Encoder reranker:

cross-encoder/ms-marco-MiniLM-L-6-v2

The reranker receives the original question and each retrieved
chunk together and produces a relevance score.

### Why Two Different Models?

The Sentence Transformer is used for fast retrieval across the
entire document collection.

The Cross-Encoder is used only on the smaller candidate set
because it is more computationally expensive.

### Final Retrieval Pipeline

User Query
→ Multi-Query Retrieval
→ ChromaDB Semantic Search
→ BM25 Keyword Search
→ Reciprocal Rank Fusion
→ Candidate Chunks
→ Cross-Encoder Reranking
→ Final Top-K Chunks

### Current Status

Advanced retrieval pipeline completed.

The system now combines semantic retrieval, keyword retrieval,
multi-query generation, metadata filtering, result fusion and
reranking.

## Step 9 - LangGraph Multi-Agent Workflow

### Why Multi-Agent?

A basic RAG system can answer simple questions about political
manifestos. However, different types of questions may require
different workflows.

For example:

- "What does BJP say about employment?" → Research
- "Compare BJP and Congress on employment." → Comparison
- "Did Congress promise an urban employment programme?" → Fact-checking

Instead of using the same workflow for every question, I added
multiple specialized agents.

The agents are useful for task routing and workflow
organization. They are not replacing the RAG system.

### Agents Used

#### 1. Task Agent

The Task Agent understands the user's question and decides
which type of task is required.

It can select:

- research
- comparison
- fact_check

Example:

User:
"What does BJP say about employment?"

Task Agent:
research

#### 2. Research Agent

The Research Agent handles questions about what a political
party or manifesto says.

It uses the existing RAG pipeline to retrieve relevant
evidence and then uses Groq to generate the answer.

Flow:

Research Agent
→ Hybrid Retrieval
→ Reranking
→ Evidence
→ Groq
→ Answer

#### 3. Comparison Agent

The Comparison Agent handles questions involving multiple
political parties.

It identifies the parties mentioned in the question and
retrieves evidence for each party separately.

Example:

"Compare BJP and Congress on employment."

Flow:

Comparison Agent
→ BJP Retrieval
→ Congress Retrieval
→ Combine Evidence
→ Groq
→ Comparison

#### 4. Fact-Check Agent

The Fact-Check Agent handles claims about political parties
and their manifesto promises.

It retrieves relevant evidence and classifies the claim as:

- Supported
- Partially Supported
- Not Supported
- Insufficient Evidence

Example:

"Did Congress promise an urban employment programme?"

Flow:

Fact-Check Agent
→ Retrieve Evidence
→ Rerank Evidence
→ Evaluate Claim
→ Groq
→ Result

### LangGraph Workflow

LangGraph is used to connect the agents into a stateful graph.

The workflow is:

User Question
→ Task Agent
→ Select Specialized Agent
→ RAG
→ Answer

The routing structure is:

Task Agent
    |
    |-- research ------> Research Agent
    |
    |-- comparison ----> Comparison Agent
    |
    |-- fact_check ----> Fact-Check Agent

Each specialized agent eventually produces the final answer.

### LangGraph State

A shared ChatState is used to pass information between nodes.

The state currently contains:

- question
- task
- context
- answer

The state changes as the question moves through the graph.

For example:

Initial state:

{
    "question": "What does BJP say about employment?"
}

After Task Agent:

{
    "question": "...",
    "task": "research"
}

After Research Agent:

{
    "question": "...",
    "task": "research",
    "context": [...],
    "answer": "..."
}

### Why LangGraph?

LangGraph provides a clear way to represent the agent workflow
as a graph.

It allows the project to have:

- Multiple agent nodes
- Conditional routing
- Shared state
- Persistent state using checkpointers
- Easier debugging and observability

### Current Architecture

User
→ Task Agent
→ Research / Comparison / Fact-Check Agent
→ Advanced RAG
→ Evidence
→ Groq
→ Final Answer

### Important Design Decision

A multi-agent architecture is not strictly necessary for a
simple RAG chatbot.

A normal RAG pipeline would be sufficient for simple questions.

The multi-agent architecture was added because the project
supports different workflows such as research, comparison and
fact-checking.

This makes the agent layer responsible for deciding how the
question should be handled, while the RAG layer remains
responsible for finding supporting evidence.

### Current Status

LangGraph multi-agent workflow implemented.

Task Agent routing and the three specialized agents are
working with the existing advanced RAG pipeline.

## Step 10 - SQLite Persistence

### Problem

The initial LangGraph workflow only maintained state while
the program was running. Conversation state would be lost
after restarting the application.

### Solution

I added LangGraph's SQLite checkpointer.

The graph is compiled with a SQLite-based checkpointer, and
each conversation is identified using a thread ID.

### Conversation Flow

User Question
→ LangGraph
→ Agent Workflow
→ Answer
→ SQLite Checkpointer

### Thread ID

Each conversation receives a unique thread ID.

Using the same thread ID allows LangGraph to access the
stored state of that conversation.

### Two Types of Storage

ChromaDB:

Stores the political knowledge base, including document
chunks, embeddings and metadata.

SQLite:

Stores LangGraph conversation/checkpoint state.

### Current Architecture

User
→ Thread ID
→ LangGraph
→ Task Agent
→ Specialized Agent
→ Advanced RAG
→ Answer
→ SQLite

### Current Status

SQLite persistence successfully integrated with LangGraph.

## Step 11 - LangSmith Observability

### Problem

The project now contains multiple agents and several retrieval
steps. Debugging the complete workflow using only terminal
output would become difficult.

### Solution

I integrated LangSmith for observability and debugging.

LangSmith is used to trace the execution of the LangGraph,
agent and LLM workflow.

### Configuration

The following environment variables are used:

LANGSMITH_API_KEY
LANGSMITH_PROJECT
LANGSMITH_TRACING

The project name is:

political-gpt

### What LangSmith Helps Monitor

- Agent execution
- LLM calls
- Prompts and responses
- Retrieval workflow
- Execution time
- Token usage where available
- Errors and failed runs

### Example Trace

User Question
→ Task Agent
→ Selected Agent
→ MQR
→ ChromaDB
→ BM25
→ RRF
→ Reranker
→ Groq
→ Final Answer

### Why LangSmith?

The multi-agent and advanced RAG workflow contains several
components. If the final answer is incorrect, LangSmith makes
it easier to identify whether the problem came from routing,
retrieval, reranking, prompting or the LLM response.

### Current Architecture

User
→ LangGraph
→ Agents
→ Advanced RAG
→ Groq

                    ↓

               LangSmith
              Observability

### Current Status

LangSmith observability integrated for the political GPT
workflow.

## Step 12 - Conversational State

### Problem

SQLite persistence was added, but the graph state did not
contain a proper message history.

This limited the chatbot's ability to understand follow-up
questions.

### Solution

I added a message-based state to LangGraph using a messages
list.

The state now maintains previous Human and AI messages.

### New State

The ChatState contains:

- messages
- question
- task
- context
- answer

### Conversation Example

User:
What does BJP say about employment?

Assistant:
BJP proposes...

User:
What about Congress?

The second question can use the previous conversation to
understand that the user is still asking about employment.

### Message Flow

Human Message
→ Task Agent
→ Specialized Agent
→ RAG
→ Groq
→ AI Message

The messages are maintained as part of the LangGraph state.

### SQLite Persistence

The message-based state is persisted using the SQLite
checkpointer.

A thread ID is used to separate different conversations.

### Current Architecture

User
→ Message State
→ Task Agent
→ Research / Comparison / Fact-Check
→ Advanced RAG
→ Groq
→ AI Response
→ SQLite Checkpoint

### Current Status

Message-based conversational state added to the LangGraph
workflow.

## Step 13 - Question Contextualization

### Problem

After adding conversational message history, users can ask
follow-up questions that are incomplete when considered
independently.

Example:

User:
What does BJP say about employment?

User:
What about Congress?

The second question does not contain enough information for
effective retrieval by itself.

### Solution

I added a question contextualization step before the Task Agent.

The contextualization step uses the previous conversation and
the current question to generate a standalone question.

Example:

Conversation:

What does BJP say about employment?

Current question:

What about Congress?

Standalone question:

What does Congress say about employment?

### Workflow

User Question
→ Conversation History
→ Question Contextualization
→ Standalone Question
→ Task Agent
→ Specialized Agent
→ Advanced RAG
→ Groq
→ Answer

### Why It Helps RAG

The retrieval system receives a complete and meaningful query
instead of a short follow-up question.

This improves the quality of MQR, semantic retrieval, BM25
retrieval and reranking.

### Current State

The ChatState now contains:

- messages
- question
- standalone_question
- task
- context
- answer

### Current Status

Question contextualization added for conversational follow-up
questions.