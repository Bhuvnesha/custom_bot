import streamlit as st
import mysql.connector

# DB connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="chatbot_db"
    )

def save_bot(name, description, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bots (name, description, notes) VALUES (%s, %s, %s)",
        (name, description, notes)
    )
    conn.commit()
    conn.close()

st.title("✨ Create a New Bot")

with st.form("create_bot_form"):
    bot_name = st.text_input("Bot Name", placeholder="Enter your bot's name")
    bot_description = st.text_area("Bot Description", placeholder="What is this bot for?")
    bot_notes = st.text_area("Notes (Reference)", placeholder="Add notes for context")

    submitted = st.form_submit_button("Create Bot")

    if submitted:
        if bot_name.strip() == "":
            st.error("⚠️ Bot name is required!")
        else:
            save_bot(bot_name, bot_description, bot_notes)
            st.success(f"✅ Bot '{bot_name}' created successfully!")
            st.switch_page("app.py")  # Navigate back to main app
