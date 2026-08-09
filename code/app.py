import uuid
import base64
from pathlib import Path

import streamlit as st

from chatbot import (
    ask_chatbot,
    save_chat,
    get_chat_history,
    get_chat_messages
)


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Political GPT",
    page_icon="🇮🇳",
    layout="wide"
)


# ============================================================
# LOAD BACKGROUND IMAGE
# ============================================================

background_path = (
    Path(__file__).parent.parent
    / "assets"
    / "political_background.png"
)


def get_background_image():

    if not background_path.exists():

        return ""

    with open(
        background_path,
        "rb"
    ) as image_file:

        encoded_image = base64.b64encode(
            image_file.read()
        ).decode()

    return encoded_image


background_image = get_background_image()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
<style>

    /* =====================================================
       MAIN BACKGROUND
       ===================================================== */

    .stApp {{

        background:
            linear-gradient(
                135deg,
                rgba(5, 8, 25, 0.94),
                rgba(20, 8, 40, 0.84),
                rgba(5, 20, 40, 0.91)
            ),
            url(
                "data:image/png;base64,{background_image}"
            );

        background-size: cover;

        background-position: center;

        background-attachment: fixed;

    }}


    /* =====================================================
       COLOR OVERLAY
       ===================================================== */

    .stApp::before {{

        content: "";

        position: fixed;

        top: 0;
        left: 0;

        width: 100%;
        height: 100%;

        background:
            linear-gradient(
                120deg,
                rgba(255, 0, 110, 0.06),
                rgba(100, 60, 255, 0.06),
                rgba(0, 210, 255, 0.06)
            );

        pointer-events: none;

        z-index: 0;

    }}


    /* =====================================================
       SIDEBAR
       ===================================================== */

    [data-testid="stSidebar"] {{

        background:
            linear-gradient(
                160deg,
                rgba(12, 10, 35, 0.98),
                rgba(32, 10, 55, 0.96),
                rgba(7, 24, 45, 0.97)
            );

        border-right:
            1px solid
            rgba(130, 100, 255, 0.35);

        box-shadow:
            8px 0 35px
            rgba(0, 0, 0, 0.35);

    }}


    /* =====================================================
       SIDEBAR TOP LINE
       ===================================================== */

    [data-testid="stSidebar"]::before {{

        content: "";

        display: block;

        height: 3px;

        width: 100%;

        background:
            linear-gradient(
                90deg,
                #ff2d75,
                #8b5cf6,
                #00d9ff
            );

    }}


    /* =====================================================
       SIDEBAR TITLE
       ===================================================== */

    [data-testid="stSidebar"] h1 {{

        font-size: 27px;

        font-weight: 800;

        background:
            linear-gradient(
                90deg,
                #ff4d8d,
                #a855f7,
                #38bdf8
            );

        -webkit-background-clip: text;

        -webkit-text-fill-color: transparent;

        letter-spacing: 1px;

    }}


    /* =====================================================
       SIDEBAR BUTTONS
       ===================================================== */

    [data-testid="stSidebar"] button {{

        border-radius: 12px;

        border:
            1px solid
            rgba(150, 100, 255, 0.25);

        background:
            linear-gradient(
                135deg,
                rgba(255, 45, 117, 0.16),
                rgba(124, 58, 237, 0.18),
                rgba(0, 200, 255, 0.12)
            );

        color: white;

        transition: all 0.2s ease;

    }}


    [data-testid="stSidebar"] button:hover {{

        border:
            1px solid
            rgba(0, 220, 255, 0.75);

        background:
            linear-gradient(
                135deg,
                rgba(255, 45, 117, 0.40),
                rgba(124, 58, 237, 0.40),
                rgba(0, 200, 255, 0.30)
            );

        transform: translateY(-1px);

        box-shadow:
            0 5px 20px
            rgba(100, 80, 255, 0.25);

    }}


    /* =====================================================
       NEW CHAT BUTTON
       ===================================================== */

    [data-testid="stSidebar"] button[kind="secondary"] {{

        background:
            linear-gradient(
                90deg,
                #ff2d75,
                #8b5cf6,
                #2563eb
            );

        border: none;

        font-weight: 700;

        box-shadow:
            0 8px 25px
            rgba(139, 92, 246, 0.30);

    }}


    /* =====================================================
       MAIN HEADING
       ===================================================== */

    .main-title {{

        font-size: 58px;

        font-weight: 900;

        letter-spacing: 5px;

        text-align: center;

        margin-top: 15px;

        margin-bottom: 0;

        background:
            linear-gradient(
                90deg,
                #00e5ff,
                #7c3aed,
                #ff3cac,
                #ff8a00
            );

        -webkit-background-clip: text;

        -webkit-text-fill-color: transparent;

        text-shadow:
            0 0 30px
            rgba(100, 80, 255, 0.25);

    }}


    /* =====================================================
       SUBTITLE
       ===================================================== */

    .technical-subtitle {{

        text-align: center;

        color:
            rgba(255, 255, 255, 0.78);

        font-size: 16px;

        letter-spacing: 2px;

        margin-top: 5px;

        margin-bottom: 20px;

    }}


    /* =====================================================
       TECH BADGES
       ===================================================== */

    .tech-container {{

        display: flex;

        justify-content: center;

        align-items: center;

        flex-wrap: wrap;

        gap: 10px;

        margin-top: 15px;

        margin-bottom: 30px;

    }}


    .tech-badge {{

        display: inline-block;

        padding: 7px 14px;

        border-radius: 20px;

        border:
            1px solid
            rgba(130, 100, 255, 0.45);

        background:
            rgba(20, 20, 40, 0.78);

        color:
            rgba(255, 255, 255, 0.90);

        font-size: 12px;

        letter-spacing: 0.5px;

        backdrop-filter: blur(10px);

        box-shadow:
            0 4px 15px
            rgba(0, 0, 0, 0.18);

    }}


    .tech-badge:hover {{

        border-color:
            rgba(0, 220, 255, 0.75);

    }}


    /* =====================================================
       CHAT MESSAGES
       ===================================================== */

    [data-testid="stChatMessage"] {{

        background:
            rgba(
                10,
                15,
                30,
                0.64
            );

        border:
            1px solid
            rgba(
                130,
                100,
                255,
                0.20
            );

        border-radius: 18px;

        padding: 8px 12px;

        backdrop-filter: blur(14px);

        box-shadow:
            0 8px 30px
            rgba(0, 0, 0, 0.18);

        margin-bottom: 10px;

    }}


    /* =====================================================
       CHAT INPUT
       ===================================================== */

    [data-testid="stChatInput"] textarea {{

        background:
            rgba(
                8,
                12,
                30,
                0.85
            ) !important;

        border:
            1px solid
            rgba(
                100,
                120,
                255,
                0.55
            ) !important;

        border-radius:
            16px !important;

        color: white !important;

        backdrop-filter: blur(15px);

    }}


    [data-testid="stChatInput"] textarea:focus {{

        border:
            1px solid
            #8b5cf6 !important;

        box-shadow:
            0 0 20px
            rgba(
                139,
                92,
                246,
                0.30
            ) !important;

    }}


    /* =====================================================
       NORMAL TEXT
       ===================================================== */

    .stMarkdown,
    p,
    label {{

        color:
            rgba(
                245,
                245,
                255,
                0.92
            );

    }}


    /* =====================================================
       DIVIDERS
       ===================================================== */

    hr {{

        border-color:
            rgba(
                150,
                120,
                255,
                0.20
            );

    }}


    /* =====================================================
       CODE / CONVERSATION ID
       ===================================================== */

    [data-testid="stSidebar"] code {{

        background:
            rgba(
                5,
                10,
                25,
                0.65
            );

        border:
            1px solid
            rgba(
                0,
                200,
                255,
                0.25
            );

        border-radius:
            8px;

    }}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# SESSION SETUP
# ============================================================

if "thread_id" not in st.session_state:

    st.session_state.thread_id = str(
        uuid.uuid4()
    )


if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# LOAD CHAT
# ============================================================

def load_chat(thread_id):

    messages = get_chat_messages(
        thread_id
    )

    st.session_state.thread_id = (
        thread_id
    )

    st.session_state.messages = (
        messages
    )


# ============================================================
# CREATE NEW CHAT
# ============================================================

def create_new_chat():

    st.session_state.thread_id = str(
        uuid.uuid4()
    )

    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "Political GPT"
    )

    st.write(
        "Manifesto Intelligence Engine"
    )

    st.caption(
        "RAG • Agents • Hybrid Search"
    )

    st.divider()


    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "＋  New Chat",
        use_container_width=True
    ):

        create_new_chat()

        st.rerun()


    st.divider()


    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    st.markdown(
        """
        <div
            style="
                color:#b8b5ff;
                font-size:13px;
                font-weight:700;
                letter-spacing:1.5px;
                text-transform:uppercase;
                margin-top:10px;
                margin-bottom:10px;
            "
        >
            ◈ CHAT HISTORY
        </div>
        """,
        unsafe_allow_html=True
    )


    chats = get_chat_history()


    if not chats:

        st.caption(
            "No previous chats"
        )


    else:

        for chat in chats:

            title = chat["title"]


            if not title:

                title = (
                    "New conversation"
                )


            if len(title) > 35:

                title = (
                    title[:35]
                    + "..."
                )


            # ------------------------------------------------
            # CURRENT CHAT
            # ------------------------------------------------

            if (
                chat["thread_id"]
                == st.session_state.thread_id
            ):

                st.button(
                    f"●  {title}",
                    key=chat["thread_id"],
                    use_container_width=True,
                    disabled=True
                )


            # ------------------------------------------------
            # PREVIOUS CHAT
            # ------------------------------------------------

            else:

                if st.button(
                    f"○  {title}",
                    key=chat["thread_id"],
                    use_container_width=True
                ):

                    load_chat(
                        chat["thread_id"]
                    )

                    st.rerun()


    st.divider()


    # --------------------------------------------------------
    # CONVERSATION ID
    # --------------------------------------------------------

    st.caption(
        "CONVERSATION ID"
    )


    st.code(
        st.session_state.thread_id
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="main-title">
        POLITICAL // GPT
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div class="technical-subtitle">
        MANIFESTO INTELLIGENCE ENGINE
        &nbsp;•&nbsp;
        INDIAN POLITICAL DOCUMENTS
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TECHNICAL BADGES
# ============================================================

st.markdown(
    """
    <div class="tech-container">
        <span class="tech-badge">
            ◈ RAG POWERED
        </span>
        <span class="tech-badge">
            ◇ HYBRID SEARCH
        </span>
        <span class="tech-badge">
            ⌁ MULTI-QUERY RETRIEVAL
        </span>
        <span class="tech-badge">
            ⚡ AGENT ROUTING
        </span>
        <span class="tech-badge">
            ✓ EVIDENCE BASED
        </span>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SHOW CURRENT MESSAGES
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Ask about a political manifesto..."
)


if question:

    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    with st.chat_message(
        "user"
    ):

        st.markdown(
            question
        )


    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Analyzing manifesto evidence..."
        ):

            result = ask_chatbot(
                question,
                st.session_state.thread_id
            )


        answer = result.get(
            "answer",
            ""
        )


        st.markdown(
            answer
        )


    # --------------------------------------------------------
    # SAVE ASSISTANT MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


    # --------------------------------------------------------
    # SAVE CONVERSATION
    # --------------------------------------------------------

    save_chat(
        thread_id=(
            st.session_state.thread_id
        ),

        messages=(
            st.session_state.messages
        )
    )