from typing import TypedDict, Annotated

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph.message import add_messages

from config import (
    GROQ_API_KEY,
    GROQ_MODEL
)

from rag import (
    hybrid_retrieval,
    rerank_results
)


# ============================================================
# CHAT STATE
# ============================================================

class ChatState(TypedDict, total=False):

    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]

    question: str
    standalone_question: str
    task: str
    context: list
    answer: str


# ============================================================
# GROQ MODEL
# ============================================================

llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0
)


# ============================================================
# GET CURRENT USER QUESTION
# ============================================================

def get_question(state: ChatState):

    messages = state.get(
        "messages",
        []
    )

    if not messages:

        return ""

    # Get only the latest human message.
    # This is important because LangGraph keeps
    # previous conversation messages.

    for message in reversed(messages):

        if message.type == "human":

            return message.content

    return ""


# ============================================================
# CHECK CASUAL QUESTION
# ============================================================

def is_casual_question(question):

    question = question.lower().strip()

    casual_questions = [

        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "hello assistant",
        "hi assistant",
        "hey assistant",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "how are you doing",
        "thanks",
        "thank you",
        "bye",
        "goodbye"
    ]

    if question in casual_questions:

        return True

    return False


# ============================================================
# FIND PARTY
# ============================================================

def find_party(question):

    question = question.lower()

    # Check more specific names first

    if (
        "bharatiya janata party" in question
        or "bjp" in question
    ):

        return "BJP"


    if (
        "indian national congress" in question
        or "congress" in question
    ):

        return "Congress"


    if (
        "trinamool congress" in question
        or "tmc" in question
    ):

        return "TMC"


    if "communist" in question:

        return "Communist Party"


    return None


# ============================================================
# GET CONVERSATION HISTORY
# ============================================================

def get_history(state: ChatState):

    messages = state.get(
        "messages",
        []
    )

    history = []

    # Do not include the latest user question.
    # It is already passed separately.

    for message in messages[:-1]:

        # Keep previous user and assistant messages
        # for contextual understanding.

        history.append(
            f"{message.type}: {message.content}"
        )

    return "\n".join(
        history
    )


# ============================================================
# QUESTION CONTEXTUALIZATION
# ============================================================

context_prompt = ChatPromptTemplate.from_template(
    """
You are a question rewriting assistant for an Indian
political manifesto chatbot.

Convert the current user question into ONE standalone
retrieval question.

The previous conversation can be used only to understand
references such as:

- "what about Congress?"
- "what about BJP?"
- "what about 2019?"
- "their policy"
- "their promise"
- "what about employment?"

Rules:

1. Preserve the user's main topic exactly.

2. If the current question mentions a political party,
   ALWAYS use the newly mentioned party.

3. Never keep the previous party when the user clearly
   changes to another party.

4. If the current question does not mention a party,
   use the previous party only when the question is clearly
   a follow-up.

5. Preserve the year if mentioned.

6. If the current question does not mention a year,
   do not invent one.

7. Do not add facts.

8. Do not answer the question.

9. Do not introduce another party.

10. If the question is already standalone, return it
    almost unchanged.

11. Return ONLY the standalone question.

Previous conversation:
{history}

Current user question:
{question}

Standalone question:
"""
)


def contextualize_question(state: ChatState):

    question = get_question(
        state
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Do not send greetings through the contextualizer.
    # --------------------------------------------------------

    if is_casual_question(question):

        print(
            "\nCasual question detected."
        )

        print(
            "Skipping contextualization."
        )

        return {

            "question": question,

            "standalone_question": question

        }


    history = get_history(
        state
    )


    prompt = context_prompt.format(
        history=history,
        question=question
    )


    response = llm.invoke(
        prompt
    )


    standalone_question = (
        response.content
        .strip()
    )


    # Remove accidental quotation marks

    standalone_question = (
        standalone_question
        .strip('"')
        .strip("'")
        .strip()
    )


    # Safety check

    if not standalone_question:

        standalone_question = question


    print(
        "\nOriginal question:"
    )

    print(
        question
    )

    print(
        "Standalone question:"
    )

    print(
        standalone_question
    )


    return {

        "question": question,

        "standalone_question":
            standalone_question

    }


# ============================================================
# TASK AGENT
# ============================================================

task_prompt = ChatPromptTemplate.from_template(
    """
You are the task agent of an Indian political manifesto
chatbot.

Determine what the user wants to do.

Available tasks:

casual:
Greetings, small talk, introductions, thanks,
goodbye, or asking what the chatbot can do.

research:
The user wants information from political party
manifestos or political documents.

comparison:
The user wants to compare two or more political parties,
policies or manifestos.

fact_check:
The user wants to verify whether a political claim,
promise or statement is supported by the documents.

Examples:

hello
-> casual

hi assistant
-> casual

how are you
-> casual

what can you do
-> casual

What does BJP say about employment?
-> research

What does Congress say about education?
-> research

Compare BJP and Congress on employment.
-> comparison

Did Congress promise an urban employment programme?
-> fact_check

Return ONLY one task:

casual
research
comparison
fact_check

Previous conversation:
{history}

Current question:
{question}
"""
)


def task_agent(state: ChatState):

    question = state.get(
        "standalone_question",
        get_question(state)
    )


    # --------------------------------------------------------
    # Directly handle obvious casual questions
    # --------------------------------------------------------

    if is_casual_question(question):

        print(
            "\nSelected task:"
        )

        print(
            "casual"
        )

        return {
            "task": "casual"
        }


    history = get_history(
        state
    )


    prompt = task_prompt.format(
        history=history,
        question=question
    )


    response = llm.invoke(
        prompt
    )


    task = (
        response.content
        .strip()
        .lower()
    )


    # --------------------------------------------------------
    # Clean model output
    # --------------------------------------------------------

    task = task.replace(
        "`",
        ""
    )

    task = task.replace(
        "*",
        ""
    )

    task = task.strip()


    # Sometimes model returns:
    # "research\n"
    # or "Task: research"

    if "casual" in task:

        task = "casual"

    elif "comparison" in task:

        task = "comparison"

    elif "fact_check" in task:

        task = "fact_check"

    elif "research" in task:

        task = "research"

    else:

        task = "research"


    print(
        "\nSelected task:"
    )

    print(
        task
    )


    return {
        "task": task
    }


# ============================================================
# CASUAL AGENT
# ============================================================

casual_prompt = ChatPromptTemplate.from_template(
    """
You are Political GPT, a friendly assistant for exploring
Indian political party manifestos.

The user is having a casual conversation.

Respond naturally, briefly and conversationally.

If the user asks what you can do, explain that you can:

- Search political party manifestos
- Answer questions using manifesto evidence
- Compare political parties and policies
- Fact-check political claims against available documents

Do NOT perform document retrieval.

Do NOT invent political information.

User:
{question}
"""
)


def casual_agent(state: ChatState):

    question = get_question(
        state
    )


    prompt = casual_prompt.format(
        question=question
    )


    response = llm.invoke(
        prompt
    )


    print(
        "\nCasual conversation"
    )


    return {

        "answer": response.content,

        "messages": [
            response
        ]

    }


# ============================================================
# FORMAT RETRIEVED EVIDENCE
# ============================================================

def format_context(results):

    if not results:

        return "No relevant evidence was retrieved."


    context_parts = []


    for i, result in enumerate(
        results,
        1
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        party = metadata.get(
            "party",
            "Unknown"
        )

        year = metadata.get(
            "year",
            "Unknown"
        )

        page = metadata.get(
            "page",
            "Unknown"
        )

        document = metadata.get(
            "document",
            "Unknown"
        )

        text = result.get(
            "text",
            ""
        )


        context_parts.append(

            f"""
SOURCE {i}

Party: {party}
Manifesto Year: {year}
Page: {page}
Document: {document}

Text:
{text}
"""
        )


    return "\n".join(
        context_parts
    )


# ============================================================
# RESEARCH AGENT
# ============================================================

research_prompt = ChatPromptTemplate.from_template(
    """
You are the research assistant of Political GPT.

Answer the user's question using the manifesto evidence
provided below.

IMPORTANT RULES:

1. Use the evidence as the primary source.

2. Do NOT use outside political knowledge.

3. Do NOT invent manifesto promises.

4. If the evidence directly answers the question,
   answer the question clearly and confidently.

5. Do NOT say "the available documents do not provide
   enough information" when the evidence contains
   relevant information.

6. Only say "Insufficient evidence" when the retrieved
   evidence genuinely does not contain information
   relevant to the question.

7. If multiple manifesto years are present, clearly
   distinguish them.

8. Mention the party, manifesto year and page number
   when useful.

9. For follow-up questions, answer the CURRENT question,
   not the previous question.

10. Keep the answer focused on the user's question.

Conversation history:
{history}

Current question:
{question}

Retrieved manifesto evidence:
{context}

Answer:
"""
)


def research_agent(state: ChatState):

    question = state.get(
        "standalone_question",
        get_question(state)
    )


    history = get_history(
        state
    )


    # --------------------------------------------------------
    # Detect party
    # --------------------------------------------------------

    party = find_party(
        question
    )


    print(
        "\nResearch question:"
    )

    print(
        question
    )

    print(
        "Detected party:"
    )

    print(
        party
    )


    # --------------------------------------------------------
    # Retrieve documents
    # --------------------------------------------------------

    results = hybrid_retrieval(

        question=question,

        k=8,

        party=party

    )


    # --------------------------------------------------------
    # Rerank documents
    # --------------------------------------------------------

    results = rerank_results(

        question=question,

        results=results,

        top_k=5

    )


    # --------------------------------------------------------
    # Format evidence
    # --------------------------------------------------------

    context = format_context(
        results
    )


    print(
        "\nEvidence chunks:"
    )

    print(
        len(results)
    )


    # --------------------------------------------------------
    # Generate answer
    # --------------------------------------------------------

    prompt = research_prompt.format(

        history=history,

        question=question,

        context=context

    )


    response = llm.invoke(
        prompt
    )


    return {

        "context": results,

        "answer": response.content,

        "messages": [
            response
        ]

    }


# ============================================================
# FIND PARTIES FOR COMPARISON
# ============================================================

party_prompt = ChatPromptTemplate.from_template(
    """
Identify the Indian political parties mentioned in the
following question.

Possible parties:

BJP
Congress
TMC
Communist Party

Return only party names, one per line.

Do not return explanations.

If a party is not mentioned, do not include it.

Conversation history:
{history}

Current question:
{question}
"""
)


def find_parties(
    question,
    history=""
):

    prompt = party_prompt.format(

        history=history,

        question=question

    )


    response = llm.invoke(
        prompt
    )


    possible_parties = [

        "BJP",

        "Congress",

        "TMC",

        "Communist Party"

    ]


    parties = []


    for line in response.content.split(
        "\n"
    ):

        line = line.strip()

        line = line.replace(
            "-",
            ""
        ).strip()

        line = line.replace(
            "`",
            ""
        ).strip()


        if line in possible_parties:

            if line not in parties:

                parties.append(
                    line
                )


    return parties


# ============================================================
# COMPARISON AGENT
# ============================================================

comparison_prompt = ChatPromptTemplate.from_template(
    """
You are a political policy comparison assistant.

Compare the political parties using ONLY the provided
manifesto evidence.

Rules:

1. Do not use outside political knowledge.

2. Do not invent promises.

3. Clearly separate each party.

4. Mention manifesto year and page number when useful.

5. If evidence for one party is missing, say so.

6. Answer only the topic asked by the user.

Conversation history:
{history}

Current question:
{question}

Manifesto evidence:
{context}

Comparison:
"""
)


def comparison_agent(state: ChatState):

    question = state.get(
        "standalone_question",
        get_question(state)
    )


    history = get_history(
        state
    )


    history_text = history


    # --------------------------------------------------------
    # Find parties
    # --------------------------------------------------------

    parties = find_parties(

        question,

        history_text

    )


    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if len(parties) < 2:

        parties = [

            "BJP",

            "Congress"

        ]


    print(
        "\nComparison parties:"
    )

    print(
        parties
    )


    # --------------------------------------------------------
    # Retrieve evidence for each party
    # --------------------------------------------------------

    all_results = []


    for party in parties:

        print(
            f"\nRetrieving documents for: {party}"
        )


        results = hybrid_retrieval(

            question=question,

            k=5,

            party=party

        )


        results = rerank_results(

            question=question,

            results=results,

            top_k=3

        )


        all_results.extend(
            results
        )


    # --------------------------------------------------------
    # Format evidence
    # --------------------------------------------------------

    context = format_context(
        all_results
    )


    # --------------------------------------------------------
    # Generate comparison
    # --------------------------------------------------------

    prompt = comparison_prompt.format(

        history=history_text,

        question=question,

        context=context

    )


    response = llm.invoke(
        prompt
    )


    return {

        "context": all_results,

        "answer": response.content,

        "messages": [
            response
        ]

    }


# ============================================================
# FACT CHECK AGENT
# ============================================================

fact_check_prompt = ChatPromptTemplate.from_template(
    """
You are a fact-checking assistant for an Indian political
manifesto chatbot.

Evaluate the user's claim using ONLY the provided manifesto
evidence.

Possible conclusions:

Supported
Partially Supported
Not Supported
Insufficient Evidence

Rules:

1. Do not use outside information.

2. Do not assume that a claim is true simply because
   it sounds politically reasonable.

3. Look for direct evidence in the manifesto.

4. If the evidence supports only part of the claim,
   use "Partially Supported".

5. If relevant evidence is absent, use
   "Insufficient Evidence".

6. Mention party, manifesto year and page when useful.

Conversation history:
{history}

Claim:
{question}

Manifesto evidence:
{context}

Fact-check result:
"""
)


def fact_check_agent(state: ChatState):

    question = state.get(
        "standalone_question",
        get_question(state)
    )


    history = get_history(
        state
    )


    # --------------------------------------------------------
    # Detect party
    # --------------------------------------------------------

    party = find_party(
        question
    )


    print(
        "\nFact-check question:"
    )

    print(
        question
    )

    print(
        "Detected party:"
    )

    print(
        party
    )


    # --------------------------------------------------------
    # Retrieve evidence
    # --------------------------------------------------------

    results = hybrid_retrieval(

        question=question,

        k=8,

        party=party

    )


    # --------------------------------------------------------
    # Rerank
    # --------------------------------------------------------

    results = rerank_results(

        question=question,

        results=results,

        top_k=5

    )


    # --------------------------------------------------------
    # Format evidence
    # --------------------------------------------------------

    context = format_context(
        results
    )


    # --------------------------------------------------------
    # Generate fact-check answer
    # --------------------------------------------------------

    prompt = fact_check_prompt.format(

        history=history,

        question=question,

        context=context

    )


    response = llm.invoke(
        prompt
    )


    return {

        "context": results,

        "answer": response.content,

        "messages": [
            response
        ]

    }