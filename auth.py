import mysql.connector
import streamlit as st
import bcrypt

# ---------- Database Connection ----------
def get_connection():
    return mysql.connector.connect(
        host="localhost",      # change if needed
        user="root",           # change to your DB user
        password="",   # change to your DB password
        database="chatbot_db"     # change to your DB name
    )

# ---------- User Management ----------
def create_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        return False
    finally:
        cur.close()
        conn.close()

def verify_user(username, password):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        st.session_state.user_id = user['id']
        st.session_state.username = user['username']
        return user
    return None
