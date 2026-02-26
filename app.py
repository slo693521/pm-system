import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ==========================================
# 1. 門神（密碼鎖）：輸入正確才能看
# ==========================================
def check_password():
    def password_entered():
        # 比對保險箱裡的密碼
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
            
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 系統存取受限")
    st.text_input("請輸入訪問密碼：", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 密碼不對喔！")
    return False

# 🛑 檢查沒過就停住
if not check_password():
    st.stop()

# ==========================================
# 2. 開始執行你的管理系統
# ==========================================

# ── 網頁基本設定 ──
st.set_page_config(page_title="進度追蹤與數據收集", layout="wide")

# ── 連接 Supabase ──
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ── 讀取資料 ──
def load_data():
    res = supabase.table("projects").select("*").order("id").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

st.title("⚙ 工程進度追蹤系統 (自動收集日期模式)")
df = load_data()

if not df.empty:
    # ── 編輯表格 ──
    st.write("★ 當你把狀態改為「製作中」並儲存，系統會自動記下今天的日期。")
    edited_df = st.data_editor(df, use_container_width=True, hide_index=True, key="main_editor")
    
    if st.button("💾 儲存並記錄起始日期", type="primary"):
        saved_count = 0
        for i, row in edited_df.iterrows():
            # 💡 核心邏輯：如果這筆被改成了製作中 (in_progress)，且原本不是製作中
            if row["status_type"] == "in_progress" and df.iloc[i]["status_type"] != "in_progress":
                # 自動填入現在的年月日
                row["started_at"] = datetime.now().strftime("%Y-%m-%d")
            
            # 把整列資料更新回 Supabase
            supabase.table("projects").update(dict(row)).eq("id", row["id"]).execute()
            saved_count += 1
            
        st.success(f"✅ 已成功儲存 {saved_count} 筆資料！")
        st.rerun()

# ── 3. 簡單的小報表 (讓你確認資料有存進去) ──
st.divider()
st.subheader("📊 已收集到的開工日期")
if not df.empty and "started_at" in df.columns:
    # 只顯示有填日期且正在製作中的案子
    working_df = df[df["started_at"] != ""]
    if not working_df.empty:
        st.table(working_df[["project_name", "status_type", "started_at"]])
    else:
        st.write("目前還沒有記錄到任何起始日期喔。")
