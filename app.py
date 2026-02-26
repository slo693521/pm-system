import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ==========================================
# 1. 密碼門神
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
        
    st.title("🔒 系統存取受限")
    st.text_input("請輸入訪問密碼：", type="password", on_change=password_entered, key="password")
    
    if "password_correct" in st.session_state:
        st.error("😕 密碼錯誤，請再試一次。")
    return False

if not check_password():
    st.stop()

# ==========================================
# 2. 系統基礎配置與樣式
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

# ── 連接 Supabase ──
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    res = supabase.table("projects").select("*").order("id").execute()
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str)
        df[col] = df[col].replace({"None": "", "nan": "", "NaN": "", "none": ""})
    return df

def refresh():
    st.cache_data.clear()
    st.rerun()

# ── 狀態設定 ──
STATUS_CONFIG = {
    "in_progress": {"label":"製作中","icon":"⚙", "bg":"#FFFF99","btn":"#e6c800","text":"#000"},
    "pending":     {"label":"待交站","icon":"📦","bg":"#CCE8FF","btn":"#2196f3","text":"#fff"},
    "not_started": {"label":"未開始","icon":"⏳","bg":"#FFFFFF","btn":"#90a4ae","text":"#fff"},
    "suspended":   {"label":"停工",  "icon":"⏸","bg":"#FFE0B2","btn":"#ff7043","text":"#fff"},
    "completed":   {"label":"已完成","icon":"✅","bg":"#F0F0F0","btn":"#757575","text":"#fff"},
}
SECTIONS = ["主要工程", "偉鴻", "材料案"]

DISPLAY_COLS = [
    "status","completion","materials","case_no","project_name","client",
    "tracking","drawing","pipe_support","welding","nde","sandblast",
    "assembly","painting","pressure_test","handover","handover_year","contact"
]

COL_CONFIG = {
    "status": st.column_config.TextColumn("施工順序"),
    "completion": st.column_config.TextColumn("完成率"),
    "materials": st.column_config.TextColumn("備料"),
    "case_no": st.column_config.TextColumn("案號"),
    "project_name": st.column_config.TextColumn("工程名稱", width="large"),
    "client": st.column_config.TextColumn("業主"),
    "tracking": st.column_config.TextColumn("備註", width="medium"),
    "handover_year": st.column_config.SelectboxColumn("年份", options=["", "114", "115", "116"]),
    "status_type": st.column_config.SelectboxColumn("狀態", options=list(STATUS_CONFIG.keys())),
}

# ── 標題與統計區 ──
today = datetime.now().strftime("%Y.%m.%d")
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a1929,#0d47a1); padding:14px 20px;border-radius:8px;margin-bottom:12px;">
  <div style="color:#fff;font-size:20px;font-weight:900;letter-spacing:2px;">⚙ 工程案執行進度管理系統</div>
  <div style="color:#90caf9;font-size:12px;margin-top:3px;">更新日期：{today} ／ Supabase 雲端資料庫 ／ 已加密連線</div>
</div>
""", unsafe_allow_html=True)

df_all = load_data()

# ── 修正：把長代碼拆短，避免 SyntaxError ──
if not df_all.empty:
    cols = st.columns(6)
    cts = df_all["status_type"].value_counts()
    
    # 安全的列表建立方式
    items = [("📋 全部", len(df_all))]
    for k, v in STATUS_CONFIG.items():
        count_val = int(cts.get(k, 0))
        label_str = f"{v['icon']} {v['label']}"
        items.append((label_str, count_val))
        
    for col, (label, val) in zip(cols, items):
        col.metric(label, val)

st.divider()

# ==========================================
# 3. 分頁與主功能
# ==========================================
page_tab1, page_tab2, page_tab3 = st.tabs(["📋 進度管理", "📊 工時分析", "⏱ 收集數據儀表板"])

# ════════════════════════════════════════════════════════
# PAGE 1：進度管理 (含自動記日期)
# ════════════════════════════════════════════════════════
with page_tab1:
    if "active_status" not in st.session_state:
        st.session_state.active_status = set()

    st.markdown("**狀態篩選**（可多選）")
    btn_cols = st.columns(6)
    
    with btn_cols[0]:
        is_all = not st.session_state.active_status
        if st.button("📋 全部", use_container_width=True, type="primary" if is_all else "secondary"):
            st.session_state.active_status = set()
            st.rerun()

    for i, (key, cfg) in enumerate(STATUS_CONFIG.items()):
        active = key in st.session_state.active_status
        count = int(df_all["status_type"].value_counts().get(key, 0)) if not df_all.empty else 0
        btn_label = f"{cfg['icon']} {cfg['label']} ({count})"
        
        with btn_cols[i+1]:
            if st.button(btn_label, use_container_width=True, type="primary" if active else "secondary", key=f"btn_{key}"):
                if active:
                    st.session_state.active_status.discard(key)
                else:
                    st.session_state.active_status.add(key)
                st.rerun()

    f1, f2, f3 = st.columns([3, 1.5, 1.5])
    with f1:
        search = st.text_input("🔍", placeholder="搜尋案號 / 工程名稱 / 業主", label_visibility="collapsed")
    with f2:
        filter_year = st.selectbox("年份", ["全部年份", "115", "114", "未填年份"], label_visibility="collapsed")
    with f3:
        filter_section = st.selectbox("分區", ["全部分區"] + SECTIONS, label_visibility="collapsed")

    df = df_all.copy() if not df_all.empty else pd.DataFrame()
    
    if not df.empty:
        if st.session_state.active_status:
            df = df[df["status_type"].isin(st.session_state.active_status)]
        if search:
            mask = (
                df["project_name"].str.contains(search, na=False) | 
                df["case_no"].str.contains(search, na=False) | 
                df["client"].str.contains(search, na=False)
            )
            df = df[mask]
        if filter_year != "全部年份":
            if filter_year == "未填年份":
                df = df[df["handover_year"] == ""]
            else:
                df = df[df["handover_year"] == filter_year]
        if filter_section != "全部分區":
            df = df[df["section"] == filter_section]

    def color_rows(row):
        bg = STATUS_CONFIG.get(row.get("status_type", ""), {}).get("bg", "#FFFFFF")
        return [f"background-color:{bg}" for _ in row]

    sections_to_show = SECTIONS if filter_section == "全部分區" else [filter_section]
    edited_data = {}

    for sec in sections_to_show:
        df_sec = df[df["section"] == sec].copy() if not df.empty else pd.DataFrame()
        if df_sec.empty and filter_section == "全部分區":
            continue

        st.markdown(f'<div class="section-header">【{sec}】 共 {len(df_sec)} 筆</div>', unsafe_allow_html=True)
        
        if df_sec.empty:
            continue

        # 安全地顯示 DataFrame
        show_df = df_sec[[c for c in DISPLAY_COLS if c in df_sec.columns]].copy()
        styled_df = show_df.assign(status_type=df_sec["status_type"].values)
        styled_df = styled_df.style.apply(color_rows, axis=1).format(na_rep="")
        
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True, 
            height=min(420, 38 + len(df_sec) * 35),
            column_config={k: v for k, v in COL_CONFIG.items() if k in show_df.columns}
        )

        with st.expander(f"✏️ 編輯【{sec}】"):
            edit_df = df_sec[[c for c in DISPLAY_COLS + ["status_type"] if c in df_sec.columns]].copy()
            # 加入隱藏的 id 欄位以供更新使用
            edit_df["id"] = df_sec["id"].values 
            
            edited = st.data_editor(
                edit_df, 
                key=f"edit_{sec}",
                column_config=COL_CONFIG,
                use_container_width=True, 
                num_rows="dynamic", 
                hide_index=True
            )
            edited_data[sec] = (df_sec, edited)

    st.divider()
    b1, b2, _ = st.columns([1, 1, 4])
    
    with b1:
        if st.button("💾 儲存所有變更", type="primary", use_container_width=True):
            try:
                saved = 0
                for sec, (old_df, new_df) in edited_data.items():
                    for i, row in new_df.iterrows():
                        row_dict = {k: ("" if pd.isna(v) or str(v) in ["None", "nan", "NaN", ""] else str(v)) for k, v in row.items()}
                        row_dict["section"] = sec
                        
                        # 處理狀態
                        if not row_dict.get("status_type") and row_dict.get("status"):
                            s = row_dict.get("status", "")
                            if "製作中" in s and "停工" not in s: row_dict["status_type"] = "in_progress"
                            elif "待交站" in s: row_dict["status_type"] = "pending"
                            elif "停工" in s: row_dict["status_type"] = "suspended"
                            elif "交站" in s or row_dict.get("completion") == "100%": row_dict["status_type"] = "completed"
                        
                        # ✨ 核心：自動記錄開始日期 ✨
                        if row_dict.get("status_type") == "in_progress":
                            # 如果是原本就有的資料，檢查舊狀態
                            if "id" in old_df.columns and i < len(old_df):
                                old_status = old_df.iloc[i].get("status_type", "")
                                if old_status != "in_progress":
                                    row_dict["started_at"] = datetime.now().strftime("%Y-%m-%d")
                            else:
                                # 如果是新增的資料，直接押上日期
                                row_dict["started_at"] = datetime.now().strftime("%Y-%m-%d")

                        # 執行更新或新增
                        if "id" in row_dict and row_dict["id"]:
                            supabase.table("projects").update(row_dict).eq("id", row_dict["id"]).execute()
                        else:
                            if "id" in row_dict: del row_dict["id"] # 新增時不需要傳遞空 id
                            supabase.table("projects").insert(row_dict).execute()
                        saved += 1
                        
                st.success(f"✅ 儲存成功！已更新 {saved} 筆資料 (包含開工日期)。")
                refresh()
            except Exception as e:
                st.error(f"儲存失敗：請檢查資料格式。錯誤細節: {e}")
                
    with b2:
        if st.button("🔄 重新整理", use_container_width=True):
            refresh()

# ════════════════════════════════════════════════════════
# PAGE 2 & 3：簡單工時收集儀表板
# ════════════════════════════════════════════════════════
with page_tab2:
    st.markdown("### 📊 系統分析區")
    st.info("💡 目前您的資料庫正在收集 `started_at` (開工日期) 數據。")
    st.write("當您在前面的「進度管理」把工程狀態改為「製作中」並存檔後，電腦就會自動幫您把開工的日期記下來。")

with page_tab3:
    st.markdown("### ⏱ 數據收集進度")
    if "started_at" in df_all.columns:
        df_working = df_all[df_all["started_at"] != ""].copy()
        if not df_working.empty:
            st.success(f"🎉 太棒了！目前已經成功收集到 **{len(df_working)}** 筆工程的開工時間。")
            
            # 整理並顯示收集到的資料
            show_working = df_working[["project_name", "status_type", "started_at"]].copy()
            show_working.columns = ["工程名稱", "目前狀態", "開工日期"]
            st.dataframe(show_working, hide_index=True, use_container_width=True)
            
            st.write("★ 收集到足夠的資料後，我們就能算出「平均完成一個案子需要幾天」囉！")
        else:
            st.info("目前還沒有收集到日期。請去把案子改成「製作中」試試看！")
    else:
        st.error("⚠️ 系統找不到儲存日期的格子！")
        st.code("請去 Supabase 的 SQL Editor 執行：\nALTER TABLE projects ADD COLUMN started_at text DEFAULT '';")
