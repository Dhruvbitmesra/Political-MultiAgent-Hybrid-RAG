import re
import chromadb

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder
)

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from rank_bm25 import BM25Okapi

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    CHROMA_PATH,
    EMBEDDING_MODEL
)


# ============================================================
# LOAD MODELS
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)


print("Loading reranker...")

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


# ============================================================
# CONNECT TO CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_collection(
    name="political_documents"
)


# ============================================================
# LOAD GROQ
# ============================================================

llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0
)


# ============================================================
# LOAD DOCUMENTS FOR BM25
# ============================================================

data = collection.get(
    include=[
        "documents",
        "metadatas"
    ]
)

documents = data["documents"]

metadatas = data["metadatas"]


print(
    f"Loaded {len(documents)} documents for BM25."
)


# ============================================================
# CLEAN TEXT FOR BM25
# ============================================================

def clean_text(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CREATE BM25 INDEX
# ============================================================

tokenized_documents = [
    clean_text(document).split()
    for document in documents
]

bm25 = BM25Okapi(
    tokenized_documents
)


# ============================================================
# NORMALIZE PARTY NAME
# ============================================================

def normalize_party(party):

    if not party:

        return None

    party = party.strip().lower()

    party_names = {

        "bjp": "BJP",

        "bharatiya janata party":
            "BJP",

        "congress":
            "Congress",

        "indian national congress":
            "Congress",

        "tmc":
            "TMC",

        "trinamool congress":
            "TMC",

        "all india trinamool congress":
            "TMC",

        "communist":
            "Communist Party",

        "communist party":
            "Communist Party"
    }

    return party_names.get(
        party,
        party
    )


# ============================================================
# MULTI QUERY RETRIEVAL PROMPT
# ============================================================

mqr_prompt = ChatPromptTemplate.from_template(
    """
You are generating search queries for an Indian political
manifesto retrieval system.

The document collection contains political party manifestos
from different years.

Generate 4 alternative search queries for the user's question.

Rules:

- Keep the exact meaning of the original question.
- Preserve the political party mentioned by the user.
- Preserve the main topic.
- Preserve the year if one is mentioned.
- Use different wording for each query.
- Use useful political and policy terminology.
- Do not introduce another political party.
- Do not introduce statistics or facts.
- Do not introduce specific policies that are not in the
  original question.
- Do not change employment into unemployment or vice versa.
- Do not answer the question.
- Keep each query concise.

Return only the queries, one per line.

Question:
{question}
"""
)


def generate_queries(question):

    prompt = mqr_prompt.format(
        question=question
    )

    response = llm.invoke(
        prompt
    )

    generated_queries = (
        response.content
        .strip()
        .split("\n")
    )

    cleaned_queries = []

    for query in generated_queries:

        query = query.strip()

        # Remove numbering such as:
        # 1.
        # 2)
        # 3-

        query = re.sub(
            r"^\s*\d+[\.\-\)\:]\s*",
            "",
            query
        )

        query = query.strip()

        if not query:

            continue

        # Avoid duplicate queries

        duplicate = False

        for existing_query in cleaned_queries:

            if (
                existing_query.lower()
                == query.lower()
            ):

                duplicate = True

                break

        if not duplicate:

            cleaned_queries.append(
                query
            )

    return cleaned_queries[:4]


# ============================================================
# CREATE CHROMADB FILTER
# ============================================================

def get_filter(
    party=None,
    year=None
):

    party = normalize_party(
        party
    )

    filters = []

    if party:

        filters.append({
            "party": party
        })

    if year:

        filters.append({
            "year": year
        })

    if len(filters) == 1:

        return filters[0]

    if len(filters) > 1:

        return {
            "$and": filters
        }

    return None


# ============================================================
# CHROMADB SEARCH
# ============================================================

def search_chroma(
    query,
    k=8,
    party=None,
    year=None
):

    party = normalize_party(
        party
    )

    query_vector = embedding_model.encode(
        [query]
    )[0]

    filter_condition = get_filter(
        party=party,
        year=year
    )

    if filter_condition:

        results = collection.query(
            query_embeddings=[
                query_vector.tolist()
            ],
            n_results=k,
            where=filter_condition
        )

    else:

        results = collection.query(
            query_embeddings=[
                query_vector.tolist()
            ],
            n_results=k
        )

    output = []

    if not results.get("documents"):

        return output

    if not results["documents"][0]:

        return output

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):

        # Extra party safety check

        if party:

            if metadata.get("party") != party:

                continue

        # Extra year safety check

        if year:

            if metadata.get("year") != year:

                continue

        output.append({

            "text": document,

            "metadata": metadata,

            "distance": float(
                distance
            )
        })

    return output


# ============================================================
# BM25 SEARCH
# ============================================================

def search_bm25(
    query,
    k=8,
    party=None,
    year=None
):

    party = normalize_party(
        party
    )

    query_words = clean_text(
        query
    ).split()

    if not query_words:

        return []

    scores = bm25.get_scores(
        query_words
    )

    results = []

    for index, score in enumerate(
        scores
    ):

        metadata = metadatas[index]

        # Party filter

        if party:

            if metadata.get("party") != party:

                continue

        # Year filter

        if year:

            if metadata.get("year") != year:

                continue

        results.append({

            "text": documents[index],

            "metadata": metadata,

            "score": float(
                score
            )
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:k]


# ============================================================
# HYBRID RETRIEVAL
# ============================================================

def hybrid_retrieval(
    question,
    k=8,
    party=None,
    year=None
):

    party = normalize_party(
        party
    )

    print(
        "\nSearching for:"
    )

    print(
        question
    )

    print(
        "\nParty filter:"
    )

    print(
        party
    )

    print(
        "\nYear filter:"
    )

    print(
        year
    )


    # ========================================================
    # GENERATE ALTERNATIVE QUERIES
    # ========================================================

    generated_queries = generate_queries(
        question
    )


    # Always keep original question

    queries = [
        question
    ]


    # Add generated queries

    for query in generated_queries:

        if query.lower() != question.lower():

            queries.append(
                query
            )


    print(
        "\nGenerated queries:"
    )

    for i, query in enumerate(
        queries,
        1
    ):

        print(
            f"{i}. {query}"
        )


    # ========================================================
    # COLLECT ALL RESULTS
    # ========================================================

    all_results = []


    # ========================================================
    # SEMANTIC SEARCH
    # ========================================================

    for query in queries:

        results = search_chroma(
            query=query,
            k=k,
            party=party,
            year=year
        )

        for rank, result in enumerate(
            results,
            1
        ):

            all_results.append({

                "text": result["text"],

                "metadata": result["metadata"],

                "method": "semantic",

                "rank": rank

            })


    # ========================================================
    # BM25 SEARCH
    # ========================================================

    for query in queries:

        results = search_bm25(
            query=query,
            k=k,
            party=party,
            year=year
        )

        for rank, result in enumerate(
            results,
            1
        ):

            all_results.append({

                "text": result["text"],

                "metadata": result["metadata"],

                "method": "bm25",

                "rank": rank

            })


    # ========================================================
    # RECIPROCAL RANK FUSION
    # ========================================================

    combined_results = {}


    for result in all_results:

        metadata = result["metadata"]

        # Use document + page + chunk
        # to identify the same chunk

        unique_id = (

            metadata.get(
                "document"
            ),

            metadata.get(
                "page"
            ),

            metadata.get(
                "chunk"
            )

        )


        if unique_id not in combined_results:

            combined_results[unique_id] = {

                "text": result["text"],

                "metadata": metadata,

                "score": 0

            }


        # RRF formula

        combined_results[
            unique_id
        ]["score"] += (

            1 / (
                60 + result["rank"]
            )

        )


    # Convert dictionary to list

    final_results = list(
        combined_results.values()
    )


    # ========================================================
    # FINAL PARTY FILTER
    # ========================================================

    if party:

        final_results = [

            result

            for result in final_results

            if result["metadata"].get(
                "party"
            ) == party

        ]


    # ========================================================
    # FINAL YEAR FILTER
    # ========================================================

    if year:

        final_results = [

            result

            for result in final_results

            if result["metadata"].get(
                "year"
            ) == year

        ]


    # ========================================================
    # SORT BY RRF
    # ========================================================

    final_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    print(
        f"\nCandidates before reranking: "
        f"{len(final_results)}"
    )


    return final_results


# ============================================================
# CROSS ENCODER + HYBRID RERANKING
# ============================================================

def rerank_results(
    question,
    results,
    top_k=5
):

    if not results:

        return []


    # ========================================================
    # STEP 1
    # Keep strongest hybrid candidates
    # ========================================================

    results = sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )


    # Only rerank the strongest candidates

    candidates = results[:20]


    # ========================================================
    # STEP 2
    # CROSS ENCODER
    # ========================================================

    pairs = []

    for result in candidates:

        pairs.append([

            question,

            result["text"]

        ])


    scores = reranker.predict(
        pairs
    )


    # Save reranker scores

    for result, score in zip(
        candidates,
        scores
    ):

        result["rerank_score"] = float(
            score
        )


    # ========================================================
    # STEP 3
    # NORMALIZE RRF SCORES
    # ========================================================

    rrf_scores = [

        result["score"]

        for result in candidates

    ]


    min_rrf = min(
        rrf_scores
    )

    max_rrf = max(
        rrf_scores
    )


    if max_rrf == min_rrf:

        for result in candidates:

            result["rrf_normalized"] = 0.5

    else:

        for result in candidates:

            result["rrf_normalized"] = (

                (
                    result["score"]
                    - min_rrf
                )

                /

                (
                    max_rrf
                    - min_rrf
                )

            )


    # ========================================================
    # STEP 4
    # NORMALIZE RERANKER SCORES
    # ========================================================

    rerank_scores = [

        result["rerank_score"]

        for result in candidates

    ]


    min_rerank = min(
        rerank_scores
    )

    max_rerank = max(
        rerank_scores
    )


    if max_rerank == min_rerank:

        for result in candidates:

            result[
                "rerank_normalized"
            ] = 0.5

    else:

        for result in candidates:

            result[
                "rerank_normalized"
            ] = (

                (
                    result["rerank_score"]
                    - min_rerank
                )

                /

                (
                    max_rerank
                    - min_rerank
                )

            )


    # ========================================================
    # STEP 5
    # COMBINE SCORES
    # ========================================================

    for result in candidates:

        result["final_score"] = (

            0.6
            * result["rrf_normalized"]

            +

            0.4
            * result["rerank_normalized"]

        )


    # ========================================================
    # STEP 6
    # FINAL SORTING
    # ========================================================

    candidates.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )


    return candidates[:top_k]


# ============================================================
# SHOW RESULTS
# ============================================================

def show_results(results):

    if not results:

        print(
            "\nNo relevant documents found."
        )

        return


    for i, result in enumerate(
        results,
        1
    ):

        print(
            "\n" + "=" * 60
        )

        print(
            f"Result {i}"
        )

        print(
            "=" * 60
        )


        print(
            "\nText:"
        )

        print(
            result["text"][:1000]
        )


        print(
            "\nMetadata:"
        )

        print(
            result["metadata"]
        )


        print(
            "\nRRF score:"
        )

        print(
            result.get(
                "score",
                0
            )
        )


        print(
            "\nReranker score:"
        )

        print(
            result.get(
                "rerank_score",
                0
            )
        )


        print(
            "\nFinal score:"
        )

        print(
            result.get(
                "final_score",
                0
            )
        )


# ============================================================
# TEST RAG
# ============================================================

if __name__ == "__main__":

    print(
        "\n=============================="
    )

    print(
        "       POLITICAL RAG TEST"
    )

    print(
        "=============================="
    )


    question = input(
        "\nEnter your question: "
    )


    party = input(
        "Enter party filter "
        "(BJP/Congress/TMC/"
        "Communist Party/None): "
    )


    # Convert "None" to Python None

    if party.lower() == "none":

        party = None


    # Normalize party

    party = normalize_party(
        party
    )


    # ========================================================
    # RETRIEVAL
    # ========================================================

    results = hybrid_retrieval(
        question=question,
        k=8,
        party=party
    )


    # ========================================================
    # RERANKING
    # ========================================================

    results = rerank_results(
        question=question,
        results=results,
        top_k=5
    )


    print(
        f"\nFinal results after reranking: "
        f"{len(results)}"
    )


    # ========================================================
    # DISPLAY
    # ========================================================

    show_results(
        results
    )