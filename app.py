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
    st.text_input("請輸入訪問密碼：", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 密碼錯誤，請再試一次。")
    return False

if not check_password():
    st.stop()

# ==========================================
# 2. 系統配置與 CSS 樣式
# ==========================================
st.set_page_config(page_title="工程案執行進度管理系統", page_icon="⚙", layout="wide", initial_sidebar_state="collapsed")

# 這裡的 """ 之前因為斷線沒閉合，這次完整了！
st.markdown("""
<style>
  .block-container { padding-top: 0.5rem !important; }
  header[data-testid="stHeader"] { background: transparent; }
  .section-header {
    background: linear-gradient(90deg, #0d2137, #1a3a5c);
    color: white; padding: 10px 16px; border-radius: 6px;
    font-size: 15px; font-weight: 800; margin: 14px 0 6px 0;
  }
  div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 900; }
  div[data-testid="stMetric"] { background:#f8faff; border-radius:8px; padding:8px; }
  .stButton > button { border-radius: 20px !important; font-size: 13px !important; }
  .legend-bar {
    display: flex; gap: 14px; flex-wrap: wrap; background: #f8f9fa; padding: 7px 14px;
    border-radius: 6px; margin-bottom: 8px; font-size: 12px; align-items: center;
  }
  .color-box {
    width: 13px; height: 13px; border-radius: 3px; border: 1px solid #bbb; display: inline-block; vertical-align: middle;
  }
</style>
""", unsafe_allow_html=True)

# ── 連接資料庫 ──
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    res = supabase.table("projects").select("*").order("id").execute()
    if not res.data: return pd.DataFrame()
    df = pd.DataFrame(res.data)
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).replace({"None":"","nan":"","NaN":"","none":""})
    return df

def refresh():
    st.cache_data.clear()
    st.rerun()

STATUS_CONFIG = {
    "in_progress": {"label":"製作中","icon":"⚙", "bg":"#FFFF99","btn":"#e6c800","text":"#000"},
    "pending":     {"label":"待交站","icon":"📦","bg":"#CCE8FF","btn":"#2196f3","text":"#fff"},
    "not_started": {"label":"未開始","icon":"⏳","bg":"#FFFFFF","btn":"#90a4ae","text":"#fff"},
    "suspended":   {"label":"停工",  "icon":"⏸","bg":"#FFE0B2","btn":"#ff7043","text":"#fff"},
    "completed":   {"label":"已完成","icon":"✅","bg":"#F0F0F0","btn":"#757575","text":"#fff"},
}
SECTIONS = ["主要工程", "偉鴻", "材料案"]
PROCESS_COLS = ["drawing","pipe_support","welding","nde","sandblast","assembly","painting","pressure_test","handover"]
PROCESS_NAMES = ["製造圖面","管撐製作","研磨點焊","焊道NDE","噴砂","組立*","噴漆","試壓","交站"]
DISPLAY_COLS = ["status","completion","materials","case_no","project_name","client","tracking","drawing","pipe_support","welding","nde","sandblast","assembly","painting","pressure_test","handover","handover_year","contact"]
COL_CONFIG = {
    "status": st.column_config.TextColumn("施工順序"), "completion": st.column_config.TextColumn("完成率"),
    "materials": st.column_config.TextColumn("備料"), "case_no": st.column_config.TextColumn("案號"),
    "project_name": st.column_config.TextColumn("工程名稱", width="large"), "client": st.column_config.TextColumn("業主"),
    "tracking": st.column_config.TextColumn("備註", width="medium"), "handover_year": st.column_config.SelectboxColumn("年份", options=["","114","115","116"]),
    "status_type": st.column_config.SelectboxColumn("狀態", options=list(STATUS_CONFIG.keys())),
}

# ── 標題與統計區 ──
today = datetime.now().strftime("%Y.%m.%d")
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a1929,#0d47a1); padding:14px 20px;border-radius:8px;margin-bottom:12px;">
  <div style="color:#fff;font-size:20px;font-weight:900;letter-spacing:2px;">⚙ 工程案執行進度管理系統</div>
  <div style="color:#90caf9;font-size:12px;margin-top:3px;">更新日期：{today} ／ Supabase 雲端資料庫 ／ 多人共用</div>
</div>
""", unsafe_allow_html=True)

df_all = load_data()

if not df_all.empty:
    cols = st.columns(6)
    cts = df_all["status_type"].value_counts()
    items = [("📋 全部", len(df_all))] + [(f"{v['icon']} {v['label']}",
