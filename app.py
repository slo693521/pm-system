import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import anthropic

st.set_page_config(
    page_title="工程案執行進度管理系統",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  .block-container { padding-top: 1rem; padding-bottom: 1rem; }
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
    font-size: 12px; align-items: center;
  }
  .color-box {
    width: 13px; height: 13px; border-radius: 3px;
    border: 1px solid #bbb; display: inline-block; vertical-align: middle;
  }
  .ai-box {
    background: linear-gradient(135deg, #e8f4f8, #f0e8ff);
    border: 1px solid #c0d8f0; border-radius: 10px;
    padding: 14px 18px; margin: 10px 0;
  }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_resource
def get_ai():
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    res = supabase.table("projects").select("*").order("id").execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df = df.fillna("").astype(str).replace("None","").replace("nan","")
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
DISPLAY_COLS = ["status","completion","materials","case_no","project_name","client",
                "tracking","drawing","pipe_support","welding","nde","sandblast",
                "assembly","painting","pressure_test","handover","handover_year",
                "notes","contact","closed","status_type"]
COL_CONFIG = {
    "status":        st.column_config.TextColumn("施工順序", width="medium"),
    "completion":    st.column_config.TextColumn("完成率", width="small"),
    "materials":     st.column_config.TextColumn("備料", width="small"),
    "case_no":       st.column_config.TextColumn("案號", width="medium"),
    "project_name":  st.column_config.TextColumn("工程名稱", width="large"),
    "client":        st.column_config.TextColumn("業主", width="small"),
    "tracking":      st.column_config.TextColumn("追蹤進度", width="medium"),
    "drawing":       st.column_config.TextColumn("製造圖面", width="small"),
    "pipe_support":  st.column_config.TextColumn("管撐製作", width="small"),
    "welding":       st.column_config.TextColumn("研磨點焊", width="medium"),
    "nde":           st.column_config.TextColumn("焊道NDE", width="small"),
    "sandblast":     st.column_config.TextColumn("噴砂", width="small"),
    "assembly":      st.column_config.TextColumn("組立*", width="small"),
    "painting":      st.column_config.TextColumn("噴漆", width="small"),
    "pressure_test": st.column_config.TextColumn("試壓", width="small"),
    "handover":      st.column_config.TextColumn("交站", width="medium"),
    "handover_year": st.column_config.SelectboxColumn("年份", options=["","114","115","116"], width="small"),
    "notes":         st.column_config.TextColumn("備註", width="medium"),
    "contact":       st.column_config.TextColumn("對應窗口", width="small"),
    "closed":        st.column_config.TextColumn("結案", width="small"),
    "status_type":   st.column_config.SelectboxColumn("狀態類型", options=list(STATUS_CONFIG.keys()), width="small"),
}

today = datetime.now().strftime("%Y.%m.%d")
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a1929,#0d47a1);
  padding:12px 20px;border-radius:8px;margin-bottom:10px;">
  <div style="color:#fff;font-size:20px;font-weight:900;letter-spacing:2px;">
    ⚙ 工程案執行進度管理系統
  </div>
  <div style="color:#90caf9;font-size:12px;margin-top:3px;">
    更新日期：{today} ／ Supabase 雲端資料庫 ／ 多人共用
  </div>
</div>
""", unsafe_allow_html=True)

df_all = load_data()

if not df_all.empty:
    cols = st.columns(6)
    cts = df_all["status_type"].value_counts()
    items = [("📋 全部", len(df_all))] + [
        (f"{v['icon']} {v['label']}", int(cts.get(k,0)))
        for k,v in STATUS_CONFIG.items()
    ]
    for col,(label,val) in zip(cols, items):
        col.metric(label, val)

st.divider()

# 狀態多選按鈕
if "active_status" not in st.session_state:
    st.session_state.active_status = set()

st.markdown("**狀態篩選**（可多選）")
btn_cols = st.columns(6)
with btn_cols[0]:
    is_all = not st.session_state.active_status
    if st.button("📋 全部" + (" ✓" if is_all else ""),
                 use_container_width=True,
                 type="primary" if is_all else "secondary"):
        st.session_state.active_status = set()
        st.rerun()

for i, (key, cfg) in enumerate(STATUS_CONFIG.items()):
    active = key in st.session_state.active_status
    count = int(df_all["status_type"].value_counts().get(key,0)) if not df_all.empty else 0
    label = f"{cfg['icon']} {cfg['label']} ({count})" + (" ✓" if active else "")
    with btn_cols[i+1]:
        if st.button(label, use_container_width=True,
                     type="primary" if active else "secondary"):
            if active:
                st.session_state.active_status.discard(key)
            else:
                st.session_state.active_status.add(key)
            st.rerun()

f1,f2,f3 = st.columns([3,1.5,1.5])
with f1:
    search = st.text_input("🔍", placeholder="搜尋案號 / 工程名稱 / 業主 / 窗口", label_visibility="collapsed")
with f2:
    filter_year = st.selectbox("年份", ["全部年份","115","114","未填年份"], label_visibility="collapsed")
with f3:
    filter_section = st.selectbox("分區", ["全部分區"]+SECTIONS, label_visibility="collapsed")

st.markdown("""
<div class="legend-bar">
  <strong>顏色：</strong>
  <span><span class="color-box" style="background:#FFFF99"></span> 製作中</span>
  <span><span class="color-box" style="background:#CCE8FF"></span> 待交站</span>
  <span><span class="color-box" style="background:#FFFFFF"></span> 未開始</span>
  <span><span class="color-box" style="background:#FFE0B2"></span> 停工</span>
  <span><span class="color-box" style="background:#F0F0F0"></span> 已完成</span>
  <span style="margin-left:auto;color:#999;font-size:11px;">★ 展開「✏️ 編輯」可修改資料</span>
</div>
""", unsafe_allow_html=True)

df = df_all.copy() if not df_all.empty else pd.DataFrame()
if not df.empty:
    if st.session_state.active_status:
        df = df[df["status_type"].isin(st.session_state.active_status)]
    if search:
        mask = (df["project_name"].str.contains(search,na=False)|
                df["case_no"].str.contains(search,na=False)|
                df["client"].str.contains(search,na=False)|
                df["contact"].str.contains(search,na=False))
        df = df[mask]
    if filter_year != "全部年份":
        df = df[df["handover_year"]==""] if filter_year=="未填年份" else df[df["handover_year"]==filter_year]
    if filter_section != "全部分區":
        df = df[df["section"]==filter_section]

st.caption(f"顯示 **{len(df)}** / {len(df_all)} 筆")

def color_rows(row):
    bg = STATUS_CONFIG.get(row.get("status_type",""),{}).get("bg","#FFFFFF")
    return [f"background-color:{bg}" for _ in row]

sections_to_show = SECTIONS if filter_section=="全部分區" else [filter_section]
edited_data = {}

for sec in sections_to_show:
    df_sec = df[df["section"]==sec].copy() if not df.empty else pd.DataFrame()
    if df_sec.empty and filter_section=="全部分區": continue

    badges = ""
    if not df_sec.empty:
        cts2 = df_sec["status_type"].value_counts()
        for k,cfg in STATUS_CONFIG.items():
            n = int(cts2.get(k,0))
            if n:
                badges += f'<span style="background:{cfg["btn"]};color:{cfg["text"]};border-radius:10px;padding:1px 9px;font-size:11px;margin-left:6px;font-weight:700;">{cfg["label"]} {n}</span>'

    st.markdown(f'<div class="section-header">【{sec}】 共 {len(df_sec)} 筆 {badges}</div>', unsafe_allow_html=True)

    if df_sec.empty:
        st.caption("此分區目前沒有資料")
        continue

    show_df = df_sec[[c for c in DISPLAY_COLS if c in df_sec.columns]].copy()
    styled = show_df.style.apply(color_rows,axis=1).format(na_rep="")
    st.dataframe(styled, use_container_width=True, hide_index=True,
                 height=min(420, 38+len(df_sec)*35),
                 column_config={k:v for k,v in COL_CONFIG.items() if k in show_df.columns})

    with st.expander(f"✏️ 編輯【{sec}】"):
        edited = st.data_editor(show_df, key=f"edit_{sec}", column_config=COL_CONFIG,
                                use_container_width=True, num_rows="dynamic", hide_index=True)
        edited_data[sec] = (df_sec["id"].tolist(), edited)

st.divider()
b1,b2,_ = st.columns([1,1,4])
with b1:
    if st.button("💾 儲存變更", type="primary", use_container_width=True):
        try:
            saved = 0
            for sec,(ids,edited_df) in edited_data.items():
                for i,row in edited_df.iterrows():
                    row_dict = {k:("" if (v is None or str(v) in ["None","nan"]) else str(v)) for k,v in row.items()}
                    row_dict["section"] = sec
                    if not row_dict.get("status_type"):
                        s = row_dict.get("status","")
                        if "製作中" in s and "停工" not in s: row_dict["status_type"]="in_progress"
                        elif "待交站" in s: row_dict["status_type"]="pending"
                        elif "停工" in s:  row_dict["status_type"]="suspended"
                        elif "交站" in s or row_dict.get("completion")=="100%": row_dict["status_type"]="completed"
                    if i < len(ids): supabase.table("projects").update(row_dict).eq("id",ids[i]).execute()
                    else: supabase.table("projects").insert(row_dict).execute()
                    saved += 1
            st.success(f"✅ 已儲存 {saved} 筆！")
            refresh()
        except Exception as e:
            st.error(f"儲存失敗：{e}")
with b2:
    if st.button("🔄 重新整理", use_container_width=True):
        refresh()

# ── AI 功能區 ──────────────────────────────────────────────
st.divider()
st.markdown("### 🤖 AI 助理")

ai_tab1, ai_tab2, ai_tab3 = st.tabs(["📊 進度摘要報告","⚠️ 風險預警","💬 自然語言查詢"])

def build_context(df):
    lines = [f"今天日期：{today}，共 {len(df)} 筆工程資料。\n"]
    for _,r in df.iterrows():
        label = STATUS_CONFIG.get(r.get("status_type",""),{}).get("label","")
        lines.append(f"- [{r['section']}] {r['project_name']} / 業主:{r['client']} / "
                     f"狀態:{label}({r['status']}) / 完成率:{r['completion']} / "
                     f"交站:{r['handover']} 年份:{r['handover_year']} / 追蹤:{r['tracking']}")
    return "\n".join(lines)

with ai_tab1:
    st.markdown("AI 自動分析所有工程狀況，產生摘要報告。")
    if st.button("🚀 產生摘要報告", type="primary"):
        with st.spinner("AI 分析中..."):
            try:
                ai = get_ai()
                msg = ai.messages.create(
                    model="claude-sonnet-4-6", max_tokens=1200,
                    messages=[{"role":"user","content":f"""你是工程進度管理助理，請根據以下資料產生繁體中文摘要報告：
1. 整體進度概況
2. 目前製作中的重點工程（前5項）
3. 待交站的工程清單
4. 需要特別注意的事項
5. 簡短建議

{build_context(df_all)}"""}])
                st.markdown(f'<div class="ai-box">{msg.content[0].text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AI 連線失敗：{e}（請在 Streamlit Secrets 新增 ANTHROPIC_API_KEY）")

with ai_tab2:
    st.markdown("AI 分析可能有風險的工程項目。")
    if st.button("🔍 分析風險", type="primary"):
        with st.spinner("AI 分析中..."):
            try:
                ai = get_ai()
                df_active = df_all[df_all["status_type"].isin(["in_progress","pending","suspended"])]
                msg = ai.messages.create(
                    model="claude-sonnet-4-6", max_tokens=1000,
                    messages=[{"role":"user","content":f"""分析以下工程的潛在風險，用繁體中文回答。
注意停工中、完成率偏低、追蹤備註有異常的工程。
用 🔴高風險 / 🟡中風險 / 🟢低風險 標示，說明原因和建議。

{build_context(df_active)}"""}])
                st.markdown(f'<div class="ai-box">{msg.content[0].text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AI 連線失敗：{e}")

with ai_tab3:
    st.markdown("用自然語言詢問任何工程相關問題。")
    examples = ["目前有哪些製作中的工程？","欣雄的工程進度如何？","完成率低於80%的工程？","預計3月交站的工程？"]
    ec = st.columns(4)
    for i,ex in enumerate(examples):
        if ec[i].button(ex, key=f"ex{i}", use_container_width=True):
            st.session_state.ai_q = ex
    question = st.text_input("輸入問題：", value=st.session_state.get("ai_q",""), placeholder="例：目前製作中有幾個工程？")
    if st.button("📨 送出", type="primary") and question:
        with st.spinner("AI 回答中..."):
            try:
                ai = get_ai()
                msg = ai.messages.create(
                    model="claude-sonnet-4-6", max_tokens=800,
                    messages=[{"role":"user","content":f"""根據以下工程資料用繁體中文回答問題，要具體列出相關工程名稱。
{build_context(df_all)}
問題：{question}"""}])
                st.markdown(f'<div class="ai-box">{msg.content[0].text}</div>', unsafe_allow_html=True)
                st.session_state.ai_q = ""
            except Exception as e:
                st.error(f"AI 連線失敗：{e}")

with st.expander("📄 匯出 PDF"):
    if st.button("產生 PDF"):
        try:
            from fpdf import FPDF; import tempfile,os
            pdf = FPDF(orientation="L",format="A3")
            pdf.set_auto_page_break(auto=True,margin=10)
            HEADERS=["施工順序","完成率","備料","案號","工程名稱","業主","追蹤進度","製造圖面","管撐","研磨點焊","NDE","噴砂","組立","噴漆","試壓","交站","年份","備註","窗口"]
            KEYS=["status","completion","materials","case_no","project_name","client","tracking","drawing","pipe_support","welding","nde","sandblast","assembly","painting","pressure_test","handover","handover_year","notes","contact"]
            WIDTHS=[20,11,7,22,55,13,28,13,11,18,11,11,11,11,11,15,9,22,11]
            PDF_BG={"in_progress":(255,255,153),"pending":(204,232,255),"not_started":(255,255,255),"suspended":(255,224,178),"completed":(240,240,240)}
            for sec in SECTIONS:
                df_sec=df_all[df_all["section"]==sec] if not df_all.empty else pd.DataFrame()
                if df_sec.empty: continue
                pdf.add_page()
                pdf.set_font("Helvetica","B",13); pdf.set_text_color(10,35,80)
                pdf.cell(0,9,f"[{sec}]  ({today})  {len(df_sec)} items",ln=True); pdf.ln(1)
                pdf.set_font("Helvetica","B",7); pdf.set_fill_color(29,71,157); pdf.set_text_color(255,255,255)
                for h,w in zip(HEADERS,WIDTHS): pdf.cell(w,7,h,border=1,fill=True,align="C")
                pdf.ln(); pdf.set_font("Helvetica","",6.5); pdf.set_text_color(30,30,30)
                for _,row in df_sec.iterrows():
                    rgb=PDF_BG.get(row.get("status_type",""),(255,255,255)); pdf.set_fill_color(*rgb)
                    for k,w in zip(KEYS,WIDTHS):
                        val=str(row.get(k,"") or "")
                        if len(val)>18: val=val[:17]+"…"
                        pdf.cell(w,6,val,border=1,fill=True)
                    pdf.ln()
            with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as tmp:
                pdf.output(tmp.name)
                with open(tmp.name,"rb") as f: pdf_bytes=f.read()
                os.unlink(tmp.name)
            st.download_button("⬇ 下載 PDF",pdf_bytes,file_name=f"工程案執行進度_{datetime.now().strftime('%Y%m%d')}.pdf",mime="application/pdf")
        except Exception as e:
            st.error(f"PDF 失敗：{e}")
