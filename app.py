import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

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
  .legend-bar {
    display: flex; gap: 16px; flex-wrap: wrap;
    background: #f8f9fa; padding: 8px 14px;
    border-radius: 6px; margin-bottom: 10px;
    font-size: 13px; align-items: center;
  }
  .legend-item { display: flex; align-items: center; gap: 5px; }
  .color-box {
    width: 14px; height: 14px; border-radius: 3px;
    border: 1px solid #ccc; display: inline-block;
  }
</style>
""", unsafe_allow_html=True)

# ── Supabase ──────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    res = supabase.table("projects").select("*").order("id").execute()
    if not res.data:
        return pd.DataFrame()
    return pd.DataFrame(res.data)

def refresh():
    st.cache_data.clear()
    st.rerun()

# ── 顏色設定 ─────────────────────────────────────────────
STATUS_BG = {
    "in_progress": "#FFFF99",
    "pending":     "#CCE8FF",
    "not_started": "#FFFFFF",
    "suspended":   "#FFE0B2",
    "completed":   "#F0F0F0",
}
STATUS_LABEL = {
    "in_progress": "製作中",
    "pending":     "待交站",
    "not_started": "未開始",
    "suspended":   "停工",
    "completed":   "已完成",
}
STATUS_MAP_REV = {v: k for k, v in STATUS_LABEL.items()}

DISPLAY_COLS = [
    "status","completion","materials","case_no","project_name","client",
    "tracking","drawing","pipe_support","welding","nde","sandblast",
    "assembly","painting","pressure_test","handover","handover_year",
    "notes","contact","closed"
]
COL_NAMES = {
    "status":"施工順序","completion":"完成率","materials":"備料",
    "case_no":"案號","project_name":"工程名稱","client":"業主",
    "tracking":"追蹤進度","drawing":"製造圖面","pipe_support":"管撐製作",
    "welding":"研磨點焊","nde":"焊道NDE","sandblast":"噴砂",
    "assembly":"組立*","painting":"噴漆","pressure_test":"試壓",
    "handover":"交站","handover_year":"年份","notes":"備註",
    "contact":"對應窗口","closed":"結案"
}

SECTIONS = ["主要工程", "偉鴻", "材料案"]

# ── 標題 ─────────────────────────────────────────────────
today = datetime.now().strftime("%Y.%m.%d")
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a1929,#0d47a1);
  padding:12px 20px;border-radius:8px;margin-bottom:12px;">
  <div style="color:#fff;font-size:20px;font-weight:900;letter-spacing:2px;">
    ⚙ 工程案執行進度管理系統
  </div>
  <div style="color:#90caf9;font-size:12px;margin-top:3px;">
    更新日期：{today} ／ 資料存於 Supabase 雲端，多人共用
  </div>
</div>
""", unsafe_allow_html=True)

# ── 載入資料 ─────────────────────────────────────────────
df_all = load_data()

# ── 統計 ─────────────────────────────────────────────────
if not df_all.empty:
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    cts = df_all["status_type"].value_counts()
    with c1: st.metric("📋 全部",    len(df_all))
    with c2: st.metric("⚙ 製作中",  int(cts.get("in_progress",0)))
    with c3: st.metric("📦 待交站",  int(cts.get("pending",0)))
    with c4: st.metric("⏳ 未開始",  int(cts.get("not_started",0)))
    with c5: st.metric("⏸ 停工",    int(cts.get("suspended",0)))
    with c6: st.metric("✅ 已完成",  int(cts.get("completed",0)))

st.divider()

# ── 篩選列 ────────────────────────────────────────────────
f1,f2,f3,f4 = st.columns([2.5, 1.5, 1.2, 1.2])
with f1:
    search = st.text_input("🔍 搜尋",
        placeholder="輸入案號 / 工程名稱 / 業主 / 窗口",
        label_visibility="collapsed")
with f2:
    filter_status = st.selectbox("狀態篩選",
        ["全部狀態","製作中","待交站","未開始","停工","已完成"],
        label_visibility="collapsed")
with f3:
    filter_year = st.selectbox("年份篩選",
        ["全部年份","115","114","未填年份"],
        label_visibility="collapsed")
with f4:
    filter_section = st.selectbox("分區篩選",
        ["全部分區"] + SECTIONS,
        label_visibility="collapsed")

# ── 顏色圖例 ──────────────────────────────────────────────
st.markdown("""
<div class="legend-bar">
  <strong>顏色說明：</strong>
  <div class="legend-item"><div class="color-box" style="background:#FFFF99"></div>製作中</div>
  <div class="legend-item"><div class="color-box" style="background:#CCE8FF"></div>待交站</div>
  <div class="legend-item"><div class="color-box" style="background:#FFFFFF"></div>未開始</div>
  <div class="legend-item"><div class="color-box" style="background:#FFE0B2"></div>停工</div>
  <div class="legend-item"><div class="color-box" style="background:#F0F0F0"></div>已完成</div>
  <span style="margin-left:auto;color:#999;font-size:12px;">★ 雙擊儲存格可直接編輯</span>
</div>
""", unsafe_allow_html=True)

# ── 套用篩選 ──────────────────────────────────────────────
df = df_all.copy() if not df_all.empty else pd.DataFrame()

if not df.empty:
    if search:
        mask = (
            df["project_name"].str.contains(search, na=False) |
            df["case_no"].str.contains(search, na=False) |
            df["client"].str.contains(search, na=False) |
            df["contact"].str.contains(search, na=False)
        )
        df = df[mask]
    if filter_status != "全部狀態":
        df = df[df["status_type"] == STATUS_MAP_REV.get(filter_status,"")]
    if filter_year != "全部年份":
        if filter_year == "未填年份":
            df = df[df["handover_year"].isna() | (df["handover_year"] == "")]
        else:
            df = df[df["handover_year"] == filter_year]
    if filter_section != "全部分區":
        df = df[df["section"] == filter_section]

st.caption(f"顯示 **{len(df)}** / {len(df_all)} 筆")

# ── 套用列顏色的函式 ──────────────────────────────────────
def color_rows(row):
    bg = STATUS_BG.get(row.get("status_type",""), "#FFFFFF")
    return [f"background-color: {bg}" for _ in row]

# ── column config ─────────────────────────────────────────
col_config = {
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
    "handover_year": st.column_config.SelectboxColumn("年份",
                        options=["","114","115","116"], width="small"),
    "notes":         st.column_config.TextColumn("備註", width="medium"),
    "contact":       st.column_config.TextColumn("對應窗口", width="small"),
    "closed":        st.column_config.TextColumn("結案", width="small"),
    "status_type":   st.column_config.SelectboxColumn("狀態",
                        options=list(STATUS_LABEL.keys()), width="small"),
}

# ── 各分區顯示 ────────────────────────────────────────────
sections_to_show = SECTIONS if filter_section == "全部分區" else [filter_section]
edited_data = {}

for sec in sections_to_show:
    df_sec = df[df["section"] == sec].copy() if not df.empty else pd.DataFrame()
    if df_sec.empty and filter_section == "全部分區":
        continue

    # 徽章
    if not df_sec.empty:
        cts2 = df_sec["status_type"].value_counts()
        badges = ""
        for st_key, st_label in [("in_progress","製作中"),("pending","待交站"),
                                   ("not_started","未開始"),("suspended","停工"),("completed","已完成")]:
            n = int(cts2.get(st_key, 0))
            colors = {"in_progress":"#c8a000","pending":"#1565c0",
                      "not_started":"#607d8b","suspended":"#e65100","completed":"#424242"}
            if n:
                badges += f'<span style="background:{colors[st_key]};color:#fff;border-radius:10px;padding:1px 9px;font-size:11px;margin-left:6px;font-weight:700;">{st_label} {n}</span>'
        total_n = len(df_sec)
    else:
        badges = ""
        total_n = 0

    st.markdown(f'<div class="section-header">【{sec}】 共 {total_n} 筆 {badges}</div>',
                unsafe_allow_html=True)

    if df_sec.empty:
        st.caption("此分區目前沒有資料")
        continue

    # 有顏色的唯讀顯示
    show_cols = DISPLAY_COLS + ["status_type"]
    styled = (df_sec[show_cols]
              .style
              .apply(color_rows, axis=1)
              .format(na_rep=""))
    st.dataframe(styled, use_container_width=True,
                 hide_index=True,
                 height=min(420, 38 + len(df_sec) * 35),
                 column_config={k: v for k, v in col_config.items() if k in show_cols})

    # 可編輯版本（展開才顯示）
    with st.expander(f"✏️ 編輯 【{sec}】"):
        edited = st.data_editor(
            df_sec[show_cols],
            key=f"edit_{sec}",
            column_config=col_config,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
        )
        edited_data[sec] = (df_sec["id"].tolist(), edited)

# ── 操作列 ───────────────────────────────────────────────
st.divider()
b1, b2, b3 = st.columns([1, 1, 4])

with b1:
    if st.button("💾 儲存變更", type="primary", use_container_width=True):
        try:
            saved = 0
            for sec, (ids, edited_df) in edited_data.items():
                for i, row in edited_df.iterrows():
                    row_dict = {k: (str(v) if v is not None else "") for k, v in row.items()}
                    row_dict["section"] = sec
                    # 自動更新 status_type
                    s = row_dict.get("status","")
                    if not row_dict.get("status_type"):
                        if "製作中" in s and "停工" not in s:
                            row_dict["status_type"] = "in_progress"
                        elif "待交站" in s:
                            row_dict["status_type"] = "pending"
                        elif "停工" in s:
                            row_dict["status_type"] = "suspended"
                        elif "交站" in s or row_dict.get("completion") == "100%":
                            row_dict["status_type"] = "completed"
                    if i < len(ids):
                        supabase.table("projects").update(row_dict).eq("id", ids[i]).execute()
                    else:
                        supabase.table("projects").insert(row_dict).execute()
                    saved += 1
            st.success(f"✅ 已儲存 {saved} 筆！")
            refresh()
        except Exception as e:
            st.error(f"儲存失敗：{e}")

with b2:
    if st.button("🔄 重新整理", use_container_width=True):
        refresh()

# ── 匯出 PDF ──────────────────────────────────────────────
with st.expander("📄 匯出 PDF"):
    if st.button("產生 PDF 並下載"):
        try:
            from fpdf import FPDF
            import tempfile, os

            pdf = FPDF(orientation="L", format="A3")
            pdf.set_auto_page_break(auto=True, margin=10)

            HEADERS = ["施工順序","完成率","備料","案號","工程名稱","業主",
                       "追蹤進度","製造圖面","管撐","研磨點焊","NDE","噴砂",
                       "組立","噴漆","試壓","交站","年份","備註","窗口"]
            KEYS    = ["status","completion","materials","case_no","project_name","client",
                       "tracking","drawing","pipe_support","welding","nde","sandblast",
                       "assembly","painting","pressure_test","handover","handover_year","notes","contact"]
            WIDTHS  = [20,11,7,22,55,13,28,13,11,18,11,11,11,11,11,15,9,22,11]

            PDF_BG = {
                "in_progress":(255,255,153), "pending":(204,232,255),
                "not_started":(255,255,255), "suspended":(255,224,178),
                "completed":(240,240,240),
            }

            for sec in SECTIONS:
                df_sec = df_all[df_all["section"] == sec] if not df_all.empty else pd.DataFrame()
                if df_sec.empty:
                    continue
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(10,35,80)
                pdf.cell(0, 9, f"[{sec}]  ({today})  {len(df_sec)} items", ln=True)
                pdf.ln(1)

                pdf.set_font("Helvetica", "B", 7)
                pdf.set_fill_color(29,71,157)
                pdf.set_text_color(255,255,255)
                for h,w in zip(HEADERS, WIDTHS):
                    pdf.cell(w, 7, h, border=1, fill=True, align="C")
                pdf.ln()

                pdf.set_font("Helvetica", "", 6.5)
                pdf.set_text_color(30,30,30)
                for _, row in df_sec.iterrows():
                    rgb = PDF_BG.get(row.get("status_type",""), (255,255,255))
                    pdf.set_fill_color(*rgb)
                    for k,w in zip(KEYS, WIDTHS):
                        val = str(row.get(k,"") or "")
                        if len(val) > 18: val = val[:17]+"…"
                        pdf.cell(w, 6, val, border=1, fill=True)
                    pdf.ln()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf.output(tmp.name)
                with open(tmp.name,"rb") as f:
                    pdf_bytes = f.read()
                os.unlink(tmp.name)

            fname = f"工程案執行進度_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button("⬇ 點此下載 PDF", pdf_bytes, file_name=fname, mime="application/pdf")
        except Exception as e:
            st.error(f"PDF 產生失敗：{e}")
