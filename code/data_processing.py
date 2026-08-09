import re
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


# ============================================================
# SETTINGS
# ============================================================

DOCUMENTS_FOLDER = Path("documents")
CHROMA_PATH = "database/chroma_db"
COLLECTION_NAME = "political_documents"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ============================================================
# DOCUMENT INFORMATION
# ============================================================

DOCUMENT_INFO = {

    "1547546675_Manifesto_2009": {
        "party": "Congress",
        "year": 2009,
        "type": "Lok Sabha Manifesto",
    },

    "bjp delhi manifesto": {
        "party": "BJP",
        "year": 2025,
        "type": "Delhi Assembly Manifesto",
    },

    "BJP-Election-english-2019": {
        "party": "BJP",
        "year": 2019,
        "type": "Lok Sabha Manifesto",
    },

    "Congress-Manifesto-English-2024-Dyoxp_4E": {
        "party": "Congress",
        "year": 2024,
        "type": "Lok Sabha Manifesto",
    },

    "election_manifesto_english_april_2024_communist": {
        "party": "Communist Party",
        "year": 2024,
        "type": "Election Manifesto",
    },

    "full_manifesto_english_07.04.2014": {
        "party": "BJP",
        "year": 2014,
        "type": "Lok Sabha Manifesto",
    },

    "Indian_National_Co_1816826a": {
        "party": "Congress",
        "year": 2014,
        "type": "Lok Sabha Manifesto",
    },

    "manifesto-english-2019": {
        "party": "Congress",
        "year": 2019,
        "type": "Lok Sabha Manifesto",
    },

    "Manifesto_English_f981dc12cc": {
        "party": "Congress",
        "year": 2025,
        "type": "Delhi Assembly Manifesto",
    },

    "Modi-Ki-Guarantee-Sankalp-Patra-English_2": {
        "party": "BJP",
        "year": 2024,
        "type": "Lok Sabha Manifesto",
    },

    "pdfName": {
        "party": "TMC",
        "year": 2014,
        "type": "Election Manifesto",
    },

    "tmc manifesto 2019.pf": {
        "party": "TMC",
        "year": 2019,
        "type": "Election Manifesto",
    },

    "tmc manifesto 2021": {
        "party": "TMC",
        "year": 2021,
        "type": "Election Manifesto",
    },
}


# ============================================================
# TEXT SPLITTER
# ============================================================

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
)


# ============================================================
# EXTRACT PAGES FROM TXT FILE
# ============================================================

def extract_pages(txt_path):
    """
    Read an extracted TXT file and recover
    page number + page text.
    """

    with open(txt_path, "r", encoding="utf-8") as file:
        text = file.read()

    pattern = (
        r"={80}\s*PAGE\s+(\d+)\s*={80}\s*"
        r"(.*?)(?=\n={80}\s*PAGE\s+\d+\s*={80}|\Z)"
    )

    matches = re.findall(
        pattern,
        text,
        re.DOTALL
    )

    pages = []

    for page_number, page_text in matches:

        page_text = page_text.strip()

        if page_text:

            pages.append({
                "page": int(page_number),
                "text": page_text
            })

    return pages


# ============================================================
# CREATE CHUNKS
# ============================================================

def create_chunks(txt_path):
    """
    Create chunks from one TXT file
    and attach document metadata.
    """

    document_name = txt_path.stem

    if document_name not in DOCUMENT_INFO:

        print(
            f"Metadata not found for: {document_name}"
        )

        return []

    document_info = DOCUMENT_INFO[document_name]

    pages = extract_pages(txt_path)

    chunks = []

    chunk_number = 0

    for page in pages:

        page_chunks = text_splitter.split_text(
            page["text"]
        )

        for chunk in page_chunks:

            chunks.append({
                "text": chunk,

                "metadata": {
                    "party": document_info["party"],
                    "year": document_info["year"],
                    "document_type": document_info["type"],
                    "document": document_name,
                    "page": page["page"],
                    "chunk": chunk_number,
                }
            })

            chunk_number += 1

    return chunks


# ============================================================
# PROCESS ALL DOCUMENTS
# ============================================================

def process_all_documents():
    """
    Process all extracted TXT files
    and return all chunks.
    """

    txt_files = list(
        DOCUMENTS_FOLDER.glob("*.txt")
    )

    print(
        f"Found {len(txt_files)} extracted text files.\n"
    )

    all_chunks = []

    for txt_file in txt_files:

        print(
            f"Processing: {txt_file.name}"
        )

        chunks = create_chunks(txt_file)

        print(
            f"Chunks created: {len(chunks)}"
        )

        all_chunks.extend(chunks)

        print()

    print("=" * 60)

    print(
        f"Total chunks created: {len(all_chunks)}"
    )

    print("=" * 60)

    return all_chunks


# ============================================================
# CREATE CHROMADB COLLECTION
# ============================================================

def create_chroma_collection():
    """
    Create or load the persistent ChromaDB collection.
    """

    Path(CHROMA_PATH).mkdir(
        parents=True,
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    return collection


# ============================================================
# STORE CHUNKS IN CHROMADB
# ============================================================

def store_in_chroma(chunks):
    """
    Generate embeddings and store chunks
    with metadata in ChromaDB.
    """

    if not chunks:

        print("No chunks found.")

        return

    print("\nLoading embedding model...")

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    collection = create_chroma_collection()

    documents = []
    metadatas = []
    ids = []

    for index, chunk in enumerate(chunks):

        documents.append(
            chunk["text"]
        )

        metadatas.append(
            chunk["metadata"]
        )

        metadata = chunk["metadata"]

        chunk_id = (
            f"{metadata['party']}_"
            f"{metadata['year']}_"
            f"{metadata['document']}_"
            f"page_{metadata['page']}_"
            f"chunk_{metadata['chunk']}"
        )

        ids.append(
            chunk_id
        )

    print(
        f"\nCreating embeddings for "
        f"{len(documents)} chunks..."
    )

    embeddings = embedding_model.encode(
        documents,
        show_progress_bar=True
    )

    print("\nStoring documents in ChromaDB...")

    collection.upsert(
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=ids
    )

    print(
        "\nDocuments successfully stored."
    )

    print(
        f"Total documents in ChromaDB: "
        f"{collection.count()}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("POLITICAL RAG - DOCUMENT INGESTION")
    print("=" * 60)

    # Step 1: Process documents
    chunks = process_all_documents()

    # Step 2: Show example
    if chunks:

        print("\nExample chunk:")
        print("-" * 60)

        print(
            chunks[0]["text"][:500]
        )

        print("\nMetadata:")
        print("-" * 60)

        print(
            chunks[0]["metadata"]
        )

    # Step 3: Create embeddings and store
    store_in_chroma(chunks)

    print("\n" + "=" * 60)
    print("INGESTION COMPLETED")
    print("=" * 60)