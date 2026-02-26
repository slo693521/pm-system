import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ==========================================
# 1. 門神（密碼鎖）
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 存取受限")
    st.text_input(
        "本 App 僅供授權人員使用，請輸入訪問密碼：", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )

    if "password_correct" in st.session_state:
        st.error("😕 密碼錯誤，請再試一次。")
        
    return False

if not check_password():
    st.stop()

# ==========================================
# 2. 你的原始系統內容 (完全保留)
# ==========================================
st.set_page_config(
    page_title="工程案執行進度管理系統",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  .block-container { padding-top: 0.5rem !important; }
  header[data-testid="stHeader"] { background: transparent; }
  .section-header {
    background: linear-gradient(90deg, #0d2137, #1a3a5c);
    color: white; padding: 10px 16px; border-radius: 6px;
    font-size: 15px; font-weight: 800; margin: 14px 0 6px 0;
    letter-spacing: 1px;
  }
  div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 900; }
  div[data-testid="stMetric"] { background:#f8faff; border-radius:8px; padding:8px; }
  .stButton > button { border-radius: 20px !important; font-size: 13px !important; }
  .legend-bar {
    display: flex; gap: 14px; flex-wrap: wrap;
    background: #f8f9fa; padding: 7px 14px;
    border-radius: 6px; margin-bottom: 8px;
    font-size:
