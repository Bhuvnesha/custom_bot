import streamlit as st
from openai import OpenAI
import mysql.connector
import pandas as pd

# ---- Database Connection ----
def get_connection():
    return mysql.connector.connect(
        host="localhost",        # change if needed
        user="root",             # your MySQL username
        password="", # your MySQL password
        database="chatbot_db"
    )

def save_message(role, content):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (role, message) VALUES (%s, %s)",
            (role, content)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"⚠️ Database Error: {e}")

def fetch_history():
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT id, role, message, created_at FROM chat_history ORDER BY created_at ASC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"⚠️ Database Error: {e}")
        return pd.DataFrame()

# ---- Sidebar Navigation ----
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["💬 Chat", "📜 History"])

# ---- Chat Page ----
if page == "💬 Chat":
    st.set_page_config(page_title="OpenRouter Bot", page_icon="🤖", layout="centered")
    st.title("🤖 OpenRouter AI Chatbot")

    # Sidebar for configuration
    st.sidebar.header("🔧 Configuration")
    api_key = "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"
    site_url = "https://example.com"
    site_name = "My Website"

    # Session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        role = "🧑 You" if msg["role"] == "user" else "🤖 Bot"
        st.chat_message(msg["role"]).markdown(f"**{role}:** {msg['content']}")

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        if not api_key or not site_url or not site_name:
            st.error("⚠️ Please configure API Key, Site URL, and Site Name in the sidebar.")
        else:
            # Save user message in memory + DB
            st.session_state.messages.append({"role": "user", "content": prompt})
            save_message("user", prompt)
            st.chat_message("user").markdown(f"**🧑 You:** {prompt}")

            try:
                # Initialize client
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )

                # API call with full history
                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": site_url,
                        "X-Title": site_name,
                    },
                    model="deepseek/deepseek-r1-0528-qwen3-8b:free",
                    messages=st.session_state.messages
                )

                # Get answer
                answer = completion.choices[0].message.content

                # Save bot response in memory + DB
                st.session_state.messages.append({"role": "assistant", "content": answer})
                save_message("assistant", answer)
                st.chat_message("assistant").markdown(f"**🤖 Bot:** {answer}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ---- History Page ----
elif page == "📜 History":
    st.set_page_config(page_title="Chat History", page_icon="📜", layout="wide")
    st.title("📜 Chat History (from MySQL)")

    df = fetch_history()

    if not df.empty:
        # ---- Filters ----
        with st.expander("🔍 Filters", expanded=True):
            col1, col2, col3 = st.columns(3)

            # Role filter
            with col1:
                role_filter = st.multiselect("Role", options=["user", "assistant"], default=["user", "assistant"])

            # Date filter
            with col2:
                date_range = st.date_input(
                    "Date Range",
                    value=(df["created_at"].min().date(), df["created_at"].max().date())
                )

            # Keyword search
            with col3:
                keyword = st.text_input("Search Keyword", placeholder="Type a word...")

        # Apply filters
        if role_filter:
            df = df[df["role"].isin(role_filter)]
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            df = df[(df["created_at"].dt.date >= start) & (df["created_at"].dt.date <= end)]
        if keyword:
            df = df[df["message"].str.contains(keyword, case=False, na=False)]

        # ---- Display ----
        st.dataframe(df, use_container_width=True, height=500)

        st.subheader("Conversation View")
        for _, row in df.iterrows():
            role = "🧑 You" if row["role"] == "user" else "🤖 Bot"
            st.chat_message(row["role"]).markdown(f"**{role}:** {row['message']}")

    else:
        st.info("No history found in the database.")
