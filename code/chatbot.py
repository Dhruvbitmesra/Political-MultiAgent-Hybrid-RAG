import os
import json
import sqlite3

from langchain_core.messages import HumanMessage

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.checkpoint.sqlite import SqliteSaver

from agents import (
    ChatState,
    contextualize_question,
    task_agent,
    casual_agent,
    research_agent,
    comparison_agent,
    fact_check_agent
)


# ============================================================
# DATABASE SETUP
# ============================================================

os.makedirs(
    "database",
    exist_ok=True
)

DATABASE_PATH = (
    "database/chat_history.db"
)


# ============================================================
# CONNECTION FOR LANGGRAPH
# ============================================================

graph_connection = sqlite3.connect(
    DATABASE_PATH,
    check_same_thread=False
)


# ============================================================
# CONNECTION FOR OUR CHAT HISTORY
# ============================================================

history_connection = sqlite3.connect(
    DATABASE_PATH,
    check_same_thread=False
)


# ============================================================
# CHAT HISTORY TABLE
# ============================================================

history_connection.execute(
    """
    CREATE TABLE IF NOT EXISTS chat_history (

        thread_id TEXT PRIMARY KEY,

        title TEXT,

        messages TEXT,

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP

    )
    """
)

history_connection.commit()


# ============================================================
# CREATE LANGGRAPH
# ============================================================

graph = StateGraph(
    ChatState
)


# ============================================================
# ADD NODES
# ============================================================

graph.add_node(
    "task_agent",
    task_agent
)

graph.add_node(
    "casual",
    casual_agent
)

graph.add_node(
    "contextualize",
    contextualize_question
)

graph.add_node(
    "research",
    research_agent
)

graph.add_node(
    "comparison",
    comparison_agent
)

graph.add_node(
    "fact_check",
    fact_check_agent
)


# ============================================================
# START OF WORKFLOW
# ============================================================

graph.add_edge(
    START,
    "task_agent"
)


# ============================================================
# CHOOSE AGENT
# ============================================================

def choose_agent(state: ChatState):

    task = state.get(
        "task",
        "research"
    )


    if task == "casual":

        return "casual"


    if task == "research":

        return "contextualize"


    if task == "comparison":

        return "contextualize"


    if task == "fact_check":

        return "contextualize"


    # Default

    return "contextualize"


# ============================================================
# TASK AGENT ROUTING
# ============================================================

graph.add_conditional_edges(
    "task_agent",

    choose_agent,

    {
        "casual": "casual",

        "contextualize":
            "contextualize"
    }
)


# ============================================================
# CHOOSE AGENT AFTER CONTEXTUALIZATION
# ============================================================

def choose_after_context(
    state: ChatState
):

    task = state.get(
        "task",
        "research"
    )


    if task == "comparison":

        return "comparison"


    if task == "fact_check":

        return "fact_check"


    return "research"


graph.add_conditional_edges(
    "contextualize",

    choose_after_context,

    {
        "research":
            "research",

        "comparison":
            "comparison",

        "fact_check":
            "fact_check"
    }
)


# ============================================================
# END OF WORKFLOW
# ============================================================

graph.add_edge(
    "casual",
    END
)

graph.add_edge(
    "research",
    END
)

graph.add_edge(
    "comparison",
    END
)

graph.add_edge(
    "fact_check",
    END
)


# ============================================================
# SQLITE CHECKPOINTER
# ============================================================

checkpointer = SqliteSaver(
    graph_connection
)


# ============================================================
# COMPILE CHATBOT
# ============================================================

chatbot = graph.compile(
    checkpointer=checkpointer
)


# ============================================================
# SAVE CHAT
# ============================================================

def save_chat(
    thread_id,
    messages
):

    if not messages:

        return


    # --------------------------------------------------------
    # First user message becomes the title
    # --------------------------------------------------------

    title = ""


    for message in messages:

        if message["role"] == "user":

            title = message["content"]

            break


    # --------------------------------------------------------
    # Keep title short
    # --------------------------------------------------------

    if len(title) > 60:

        title = (
            title[:60]
            + "..."
        )


    # --------------------------------------------------------
    # Convert messages to JSON
    # --------------------------------------------------------

    messages_json = json.dumps(
        messages,
        ensure_ascii=False
    )


    # --------------------------------------------------------
    # Save to database
    # --------------------------------------------------------

    history_connection.execute(
        """
        INSERT OR REPLACE INTO chat_history
        (
            thread_id,
            title,
            messages,
            updated_at
        )
        VALUES
        (
            ?,
            ?,
            ?,
            CURRENT_TIMESTAMP
        )
        """,
        (
            thread_id,
            title,
            messages_json
        )
    )


    history_connection.commit()


# ============================================================
# GET ALL PREVIOUS CHATS
# ============================================================

def get_chat_history():

    cursor = history_connection.execute(
        """
        SELECT
            thread_id,
            title,
            created_at,
            updated_at

        FROM chat_history

        ORDER BY updated_at DESC
        """
    )


    chats = []


    for row in cursor.fetchall():

        chats.append({

            "thread_id": row[0],

            "title": row[1],

            "created_at": row[2],

            "updated_at": row[3]

        })


    return chats


# ============================================================
# GET MESSAGES OF ONE CHAT
# ============================================================

def get_chat_messages(
    thread_id
):

    cursor = history_connection.execute(
        """
        SELECT messages

        FROM chat_history

        WHERE thread_id = ?
        """,
        (
            thread_id,
        )
    )


    row = cursor.fetchone()


    if row is None:

        return []


    return json.loads(
        row[0]
    )


# ============================================================
# DELETE CHAT
# ============================================================

def delete_chat(
    thread_id
):

    history_connection.execute(
        """
        DELETE FROM chat_history

        WHERE thread_id = ?
        """,
        (
            thread_id,
        )
    )


    history_connection.commit()


# ============================================================
# ASK CHATBOT
# ============================================================

def ask_chatbot(
    question,
    thread_id
):

    config = {

        "configurable": {

            "thread_id":
                thread_id

        }

    }


    result = chatbot.invoke(

        {
            "messages": [

                HumanMessage(
                    content=question
                )

            ]
        },

        config=config

    )


    return result


# ============================================================
# TERMINAL TESTING
# ============================================================

if __name__ == "__main__":

    print(
        "\n=============================="
    )

    print(
        "       POLITICAL GPT"
    )

    print(
        "=============================="
    )


    thread_id = input(
        "\nEnter conversation ID: "
    )


    print(
        "\nType 'exit' to stop."
    )


    while True:

        question = input(
            "\nYou: "
        )


        if question.lower() == "exit":

            break


        result = ask_chatbot(
            question,
            thread_id
        )


        print(
            "\n------------------------------"
        )


        print(
            "Task selected:"
        )


        print(
            result.get(
                "task",
                "unknown"
            )
        )


        print(
            "\nBot:"
        )


        print(
            result.get(
                "answer",
                ""
            )
        )


        print(
            "------------------------------"
        )