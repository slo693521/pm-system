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
            
    if st.session_state.get("password_correct", False): return True
        
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
st.set_page_config(page_title="工程案執行進度管理系統", page_icon="⚙", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  .block-container { padding-top: 0.5rem !important; }
  header[data-testid="stHeader"] { background: transparent; }
  .section-header {
    background: linear-gradient(90deg, #0d2137, #1a3a5c); color: white; padding: 10px 16px; border-radius: 6px; font-weight: 800;
  }
  div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 900; }
  div[data-testid="stMetric"] { background:#f8faff; border-radius:8px; padding:8px; border: 1px solid #eef; }
  .stButton > button { border-radius: 20px !important; font-size: 13px !important; }
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
    if not res.data: return pd.DataFrame()
    df = pd.DataFrame(res.data)
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).replace({"None": "", "nan": "", "NaN": "", "none": ""})
    return df

# ✨ 修復 1：精準清除快取，確保圖表 100% 連動更新
def refresh():
    load_data.clear()
    try:
        load_work_logs.clear()
    except:
        pass
    st.rerun()

# ── 狀態與欄位設定 ──
STATUS_CONFIG = {
    "in_progress": {"label":"製作中","icon":"⚙", "bg":"#FFFF99","text":"#000"},
    "pending":     {"label":"待交站","icon":"📦","bg":"#CCE8FF","text":"#000"},
    "not_started": {"label":"未開始","icon":"⏳","bg":"#FFFFFF","text":"#000"},
    "suspended":   {"label":"停工",  "icon":"⏸","bg":"#FFE0B2","text":"#000"},
    "completed":   {"label":"已完成","icon":"✅","bg":"#F0F0F0","text":"#000"},
}
SECTIONS = ["主要工程", "偉鴻", "材料案"]
DISPLAY_COLS = ["status","completion","materials","case_no","project_name","client","tracking","drawing","pipe_support","welding","nde","sandblast","assembly","painting","pressure_test","handover","handover_year","contact"]
COL_CONFIG = {
    "status": st.column_config.TextColumn("施工順序"), "completion": st.column_config.TextColumn("完成率"),
    "materials": st.column_config.TextColumn("備料"), "case_no": st.column_config.TextColumn("案號"),
    "project_name": st.column_config.TextColumn("工程名稱", width="large"), "client": st.column_config.TextColumn("業主"),
    "tracking": st.column_config.TextColumn("備註", width="medium"), "handover_year": st.column_config.SelectboxColumn("年份", options=["", "114", "115", "116"]),
    "status_type": st.column_config.SelectboxColumn("狀態", options=list(STATUS_CONFIG.keys())),
}

today = datetime.now().strftime("%Y.%m.%d")
st.markdown(f"### ⚙ 工程案執行進度管理系統 ({today})")

df_all = load_data()
if not df_all.empty:
    cols = st.columns(6)
    cts = df_all["status_type"].value_counts()
    items = [("📋 全部", len(df_all))]
    for k, v in STATUS_CONFIG.items(): items.append((f"{v['icon']} {v['label']}", int(cts.get(k, 0))))
    for col, (label, val) in zip(cols, items): col.metric(label, val)

st.divider()

# ==========================================
# 3. 分頁與主功能
# ==========================================
page_tab1, page_tab2, page_tab3 = st.tabs(["📋 進度管理", "📊 工時分析", "⏱ 收集數據儀表板"])

with page_tab1:
    st.write("💡 提示：在表格中修改資料後，請務必點擊下方的「💾 儲存所有變更」，上方的數字和分析圖表才會同步更新！")
    
    if "active_status" not in st.session_state: st.session_state.active_status = set()
    btn_cols = st.columns(6)
    with btn_cols[0]:
        is_all = not st.session_state.active_status
        if st.button("📋 全部", use_container_width=True, type="primary" if is_all else "secondary"):
            st.session_state.active_status = set(); st.rerun()

    for i, (key, cfg) in enumerate(STATUS_CONFIG.items()):
        active = key in st.session_state.active_status
        count = int(df_all["status_type"].value_counts().get(key, 0)) if not df_all.empty else 0
        if st.button(f"{cfg['icon']} {cfg['label']} ({count})", use_container_width=True, type="primary" if active else "secondary", key=f"btn_{key}"):
            if active: st.session_state.active_status.discard(key)
            else: st.session_state.active_status.add(key)
            st.rerun()

    f1, f2, f3 = st.columns([3, 1.5, 1.5])
    with f1: search = st.text_input("🔍", placeholder="搜尋案號 / 工程名稱 / 業主", label_visibility="collapsed")
    with f2: filter_year = st.selectbox("年份", ["全部年份", "115", "114", "未填年份"], label_visibility="collapsed")
    with f3: filter_section = st.selectbox("分區", ["全部分區"] + SECTIONS, label_visibility="collapsed")

    df = df_all.copy() if not df_all.empty else pd.DataFrame()
    if not df.empty:
        if st.session_state.active_status: df = df[df["status_type"].isin(st.session_state.active_status)]
        if search: df = df[df["project_name"].str.contains(search, na=False) | df["case_no"].str.contains(search, na=False) | df["client"].str.contains(search, na=False)]
        if filter_year != "全部年份": df = df[df["handover_year"] == ""] if filter_year == "未填年份" else df[df["handover_year"] == filter_year]
        if filter_section != "全部分區": df = df[df["section"] == filter_section]

    def color_rows(row):
        bg = STATUS_CONFIG.get(row.get("status_type", ""), {}).get("bg", "#FFFFFF")
        return [f"background-color:{bg}" for _ in row]

    sections_to_show = SECTIONS if filter_section == "全部分區" else [filter_section]
    edited_data = {}

    for sec in sections_to_show:
        df_sec = df[df["section"] == sec].copy() if not df.empty else pd.DataFrame()
        if df_sec.empty: continue
        st.markdown(f'<div class="section-header">【{sec}】 共 {len(df_sec)} 筆</div>', unsafe_allow_html=True)
        
        show_df = df_sec[[c for c in DISPLAY_COLS if c in df_sec.columns]].copy()
        styled_df = show_df.assign(status_type=df_sec["status_type"].values).style.apply(color_rows, axis=1).format(na_rep="")
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=min(420, 38 + len(df_sec) * 35), column_config={k: v for k, v in COL_CONFIG.items() if k in show_df.columns})

        with st.expander(f"✏️ 編輯【{sec}】"):
            edit_df = df_sec[[c for c in DISPLAY_COLS + ["status_type"] if c in df_sec.columns]].copy()
            edit_df["id"] = df_sec["id"].values 
            edited = st.data_editor(edit_df, key=f"edit_{sec}", column_config=COL_CONFIG, use_container_width=True, num_rows="dynamic", hide_index=True)
            edited_data[sec] = (df_sec, edited)

    st.divider()
    b1, b2, b3 = st.columns([2, 1, 3])
    
    with b1:
        if st.button("💾 儲存所有變更", type="primary", use_container_width=True):
            with st.spinner("正在儲存並更新圖表..."):
                try:
                    saved = 0
                    for sec, (old_df, new_df) in edited_data.items():
                        for i, row in new_df.iterrows():
                            row_dict = {k: ("" if pd.isna(v) or str(v) in ["None", "nan", "NaN", ""] else str(v)) for k, v in row.items()}
                            row_dict["section"] = sec
                            if not row_dict.get("status_type") and row_dict.get("status"):
                                s = row_dict.get("status", "")
                                if "製作中" in s and "停工" not in s: row_dict["status_type"] = "in_progress"
                                elif "待交站" in s: row_dict["status_type"] = "pending"
                                elif "停工" in s: row_dict["status_type"] = "suspended"
                                elif "交站" in s or row_dict.get("completion") == "100%": row_dict["status_type"] = "completed"
                            
                            if row_dict.get("status_type") == "in_progress":
                                if "id" in old_df.columns and i < len(old_df):
                                    old_status = old_df.iloc[i].get("status_type", "")
                                    if old_status != "in_progress": row_dict["started_at"] = datetime.now().strftime("%Y-%m-%d")
                                else:
                                    row_dict["started_at"] = datetime.now().strftime("%Y-%m-%d")

                            if "id" in row_dict and row_dict["id"]: supabase.table("projects").update(row_dict).eq("id", row_dict["id"]).execute()
                            else:
                                if "id" in row_dict: del row_dict["id"]
                                supabase.table("projects").insert(row_dict).execute()
                            saved += 1
                    st.success(f"✅ 儲存成功！圖表已同步更新。")
                    refresh()
                except Exception as e:
                    st.error(f"儲存失敗：{e}")
                
    with b2:
        if st.button("🔄 重新整理", use_container_width=True): refresh()
        
    with b3:
        with st.expander("📄 匯出 PDF (支援中文)"):
            if st.button("產生 PDF", use_container_width=True):
                try:
                    from fpdf import FPDF
                    import tempfile, os, urllib.request

                    # ✨ 修復 2：改用 Google Fonts 官方的標準 TTF 字型
                    font_path = "/tmp/NotoSansTC-Regular.ttf"
                    if not os.path.exists(font_path):
                        with st.spinner("首次使用：下載中文字型中（約需5秒）..."):
                            urllib.request.urlretrieve(
                                "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf",
                                font_path
                            )

                    pdf = FPDF(orientation="L", format="A3")
                    pdf.set_auto_page_break(auto=True, margin=10)
                    pdf.add_font("Chinese", "", font_path, uni=True)
                    pdf.add_font("Chinese", "B", font_path, uni=True)

                    HEADERS=["施工順序","完成率","備料","案號","工程名稱","業主","備註","製造圖面","管撐","研磨點焊","NDE","噴砂","組立","噴漆","試壓","交站","年份","窗口"]
                    KEYS=["status","completion","materials","case_no","project_name","client","tracking","drawing","pipe_support","welding","nde","sandblast","assembly","painting","pressure_test","handover","handover_year","contact"]
                    WIDTHS=[20,11,7,22,55,13,30,13,11,18,11,11,11,11,11,15,9,13]
                    PDF_BG={"in_progress":(255,255,153),"pending":(204,232,255),"not_started":(255,255,255),"suspended":(255,224,178),"completed":(240,240,240)}

                    for sec in SECTIONS:
                        df_sec = df_all[df_all["section"]==sec] if not df_all.empty else pd.DataFrame()
                        if df_sec.empty: continue
                        pdf.add_page()
                        pdf.set_font("Chinese","B",13)
                        pdf.set_text_color(10,35,80)
                        pdf.cell(0,9,f"【{sec}】  ({today})  共{len(df_sec)}筆",ln=True)
                        pdf.ln(1)
                        pdf.set_font("Chinese","B",7)
                        pdf.set_fill_color(29,71,157); pdf.set_text_color(255,255,255)
                        for h,w in zip(HEADERS,WIDTHS): pdf.cell(w,7,h,border=1,fill=True,align="C")
                        pdf.ln()
                        pdf.set_font("Chinese","",6.5); pdf.set_text_color(30,30,30)
                        for _,row in df_sec.iterrows():
                            rgb = PDF_BG.get(row.get("status_type",""),(255,255,255))
                            pdf.set_fill_color(*rgb)
                            for k,w in zip(KEYS,WIDTHS):
                                val = str(row.get(k,"") or "")
                                if len(val)>18: val = val[:17]+"…"
                                pdf.cell(w,6,val,border=1,fill=True)
                            pdf.ln()

                    with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as tmp:
                        pdf.output(tmp.name)
                        with open(tmp.name,"rb") as f: pdf_bytes=f.read()
                        os.unlink(tmp.name)
                    
                    st.download_button("⬇ 點此下載完美版 PDF", pdf_bytes, file_name=f"工程進度_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
                    st.success("PDF 產生成功！")
                except Exception as e:
                    st.error(f"PDF 失敗：請確認已在 requirements.txt 中加入 fpdf2！錯誤細節：{e}")

with page_tab2:
    st.markdown("### 📊 系統分析區")
    st.info("💡 目前您的資料庫正在收集 `started_at` (開工日期) 數據。")

with page_tab3:
    st.markdown("### ⏱ 數據收集進度")
    if "started_at" in df_all.columns:
        df_working = df_all[df_all["started_at"] != ""].copy()
        if not df_working.empty:
            st.success(f"🎉 成功收集到 **{len(df_working)}** 筆工程開工時間。")
            show_working = df_working[["project_name", "status_type", "started_at"]].copy()
            show_working.columns = ["工程名稱", "目前狀態", "開工日期"]
            st.dataframe(show_working, hide_index=True, use_container_width=True)
        else: st.info("目前還沒有收集到日期。去把案子改成「製作中」試試看！")
    else:
        st.error("⚠️ 系統找不到儲存日期的格子！請在 Supabase 執行: ALTER TABLE projects ADD COLUMN started_at text DEFAULT '';")
