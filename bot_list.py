import streamlit as st
import mysql.connector

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "chatbot_db"
}


# 🔹 Fetch all bots from DB
def get_all_bots():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bots ORDER BY created_at DESC")
    bots = cursor.fetchall()
    conn.close()
    return bots


st.title("🤖 My Bots")

bots = get_all_bots()

if not bots:
    st.info("No bots created yet. Go to 'Create Bot' page to add one.")
else:
    for bot in bots:
        with st.container():
            st.subheader(bot["name"])
            st.write(bot["description"])
            if bot["notes"]:
                st.caption(f"📝 {bot['notes']}")

            # Button to select this bot
            if st.button(f"Chat with {bot['name']}", key=f"select_{bot['id']}"):
                st.session_state["selected_bot_id"] = bot["id"]
                st.success(f"✅ Selected {bot['name']} as active bot.")
                st.switch_page("main.py")  # Navigate to chat page
