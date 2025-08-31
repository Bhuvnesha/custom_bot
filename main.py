import streamlit as st
from openai import OpenAI
import mysql.connector
import pandas as pd

from login import login_signup_page

# Initialize session state variables if they don't exist yet
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None


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

def save_bot(bot_name, bot_description, bot_notes, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bots (name, description, notes, user_id) VALUES (%s, %s, %s, %s)",
        (bot_name, bot_description, bot_notes, user_id)
    )
    conn.commit()
    conn.close()

# 🔹 Load selected bot details from DB
def get_bot_details(bot_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bots WHERE id = %s", (bot_id,))
    bot = cursor.fetchone()
    conn.close()
    return bot

def get_all_bots(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bots WHERE user_id=%s", (user_id,))
    bots = cursor.fetchall()
    conn.close()
    return bots

def save_chat(user_id, bot_id, user_message, bot_response):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chats (user_id, bot_id, user_message, bot_response) VALUES (%s, %s, %s, %s)",
        (user_id, bot_id, user_message, bot_response),
    )
    conn.commit()
    conn.close()


def get_chat_history(user_id, bot_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if bot_id:
        cursor.execute("SELECT user_message, bot_response, timestamp FROM chats WHERE user_id=%s AND bot_id=%s ORDER BY timestamp DESC", (user_id, bot_id))
    else:
        cursor.execute("SELECT user_message, bot_response, timestamp FROM chats WHERE user_id=%s ORDER BY timestamp DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def truncate_with_link(text, key, max_chars=50):
    """Truncate long text with a 'Read more' toggle."""
    if len(text) > max_chars:
        if st.session_state.get(f"show_full_{key}", False):
            if st.button(f"Read less {key}", key=f"less_{key}"):
                st.session_state[f"show_full_{key}"] = False
            return text
        else:
            short_text = text[:max_chars] + "..."
            if st.button(f"Read more {key}", key=f"more_{key}"):
                st.session_state[f"show_full_{key}"] = True
            return short_text
    return text

def format_with_readmore(text, max_chars=50):
    """Format text with inline read more/read less using <details> and <br> for newlines."""
    if not text:
        return ""

    # Normalize text: strip leading/trailing \n, then replace remaining with <br>
    text = str(text).strip("\n").replace("\n", "<br>")

    if len(text) > max_chars:
        short = text[:max_chars] + "..."
        return f"""
        <details>
            <summary>{short} <span style='color:blue;cursor:pointer;'>Read more</span></summary>
            {text}
        </details>
        """
    return text

# At the top of main app
if "user" not in st.session_state:
    login_signup_page()
    st.stop()

# After login:
st.sidebar.write(f"👤 Logged in as: **{st.session_state['user']['username']}**")
if st.sidebar.button("Logout"):
    del st.session_state["user"]
    st.rerun()

# ✅ Your bot/chat UI continues here...




# ---- Sidebar Navigation ----
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["💬 Chat", "📜 History", "Create Bot"])

# ---- Chat Page ----
if page == "💬 Chat":
    st.set_page_config(page_title="OpenRouter Bot", page_icon="🤖", layout="centered")
    st.title("🤖 OpenRouter AI Chatbot")

    # Sidebar for configuration
    st.sidebar.header("🔧 Configuration")
    api_key = "<api_key>"
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

            # 🔹 Load selected bot details from DB
            def get_bot_details(bot_id):
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM bots WHERE id = %s", (bot_id,))
                bot = cursor.fetchone()
                conn.close()
                return bot

            # 🔹 Before sending messages to the API, prepend system prompt
            if "selected_bot_id" in st.session_state:
                bot = get_bot_details(st.session_state["selected_bot_id"])
                if bot:
                    system_prompt = f"You are {bot['name']}. {bot['description']}\nNotes: {bot['notes']}"
                    bot_prompt = system_prompt + " " + prompt
                    if not any(m["role"] == "system" for m in st.session_state.messages):
                        st.session_state.messages.insert(0, {"role": "system", "content": bot_prompt})

                # Save user message (memory + DB)
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.chat_message("user").markdown(f"**🧑 You:** {prompt}")

            try:
                # Initialize client
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )

                # Show loading indicator while bot responds (streaming word by word)
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Bot is typing..."):
                        response_placeholder = st.empty()
                        full_response = ""

                        stream = client.chat.completions.create(
                            extra_headers={
                                "HTTP-Referer": site_url,
                                "X-Title": site_name,
                            },
                            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
                            messages=st.session_state.messages,
                            stream=True
                        )

                        for chunk in stream:
                            delta = chunk.choices[0].delta
                            if delta and delta.content is not None:
                                word = delta.content
                                full_response += word
                                response_placeholder.markdown(f"**🤖 Bot:** {full_response}▌")

                        response_placeholder.markdown(f"**🤖 Bot:** {full_response}")

                # Save bot response (memory + DB)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

                # ✅ Save chat in MySQL
                if "user_id" in st.session_state and "selected_bot_id" in st.session_state:
                    save_chat(
                        user_id=st.session_state["user_id"],
                        bot_id=st.session_state["selected_bot_id"],
                        user_message=prompt,
                        bot_response=full_response
                    )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# ---- History Page ----
elif page == "📜 History":
    st.set_page_config(page_title="Chat History", page_icon="📜", layout="wide")
    # st.title("📜 Chat History (from MySQL)")
    if "user_id" in st.session_state:
        st.subheader("💬 Chat History")

        chats = get_chat_history(st.session_state.user_id,
                                 st.session_state.selected_bot if "selected_bot" in st.session_state else None)

        if chats:
            df = pd.DataFrame(chats, columns=["User Message", "Bot Response", "Time"])

            # Apply read more formatting
            df["User Message"] = df["User Message"].apply(lambda x: format_with_readmore(str(x)))
            df["Bot Response"] = df["Bot Response"].apply(lambda x: format_with_readmore(str(x)))

            # Add copy button for each bot response
            df["Copy Code"] = df["Bot Response"].apply(
                lambda x: f"""
                <button onclick="navigator.clipboard.writeText(`{x.replace('<br>', '\\n')}`)" 
                        style="padding:4px 8px; border:1px solid #ccc; border-radius:4px; background:#eee; cursor:pointer;">
                    Copy
                </button>
                """
            )

            # Render as HTML table
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

        else:
            st.info("No chat history yet.")


# --- Create Bot Page ---
if page == "Create Bot":
    st.title("✨ Create a New Bot")

    with st.form("create_bot_form", clear_on_submit=True):
        bot_name = st.text_input("🤖 Bot Name", max_chars=50, placeholder="E.g. Project Helper Bot")
        bot_description = st.text_area("📖 Bot Description", height=100, placeholder="What does this bot do?")
        bot_notes = st.text_area("📝 Notes / References", height=150, placeholder="Any special instructions, references, or knowledge base...")

        submitted = st.form_submit_button("✅ Save Bot")

        if submitted:
            if bot_name.strip() == "":
                st.error("Bot name is required!")
            else:
                save_bot(bot_name, bot_description, bot_notes, st.session_state.user_id)
                st.success(f"🎉 Bot '{bot_name}' created successfully!")
                st.session_state.page = "Chat"  # Switch back to Chat after creation

# 🔹 Sidebar Dropdown
with st.sidebar:
    st.markdown("### 🤖 Select Bot")

    bots = get_all_bots(st.session_state.user_id)

    # Build list with "Default Bot" as first option
    bot_names = ["Default Bot"] + [b["name"] for b in bots]
    bot_ids = [None] + [b["id"] for b in bots]   # None for Default Bot

    # Figure out default selection index
    default_index = 0
    if "selected_bot_id" in st.session_state and st.session_state["selected_bot_id"] in bot_ids:
        default_index = bot_ids.index(st.session_state["selected_bot_id"])

    selected_bot = st.selectbox("Choose your bot:", bot_names, index=default_index)

    # Update session state
    selected_bot_id = bot_ids[bot_names.index(selected_bot)]
    st.session_state["selected_bot_id"] = selected_bot_id
    st.session_state["selected_bot_name"] = selected_bot

    # Display active bot
    st.success(f"🟢 Active Bot: {st.session_state['selected_bot_name']}")




