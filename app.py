import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# ── 頁面設定 ────────────────────────────────────────────
st.set_page_config(
    page_title="工程案執行進度管理系統",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 自訂 CSS ────────────────────────────────────────────
st.markdown("""
<style>
  .main { padding: 0.5rem 1rem; }
  .stDataEditor { font-size: 13px; }
  div[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 900; }
  .section-header {
    background: linear-gradient(90deg, #0d2137, #1a3a5c);
    color: white; padding: 8px 16px; border-radius: 6px;
    font-size: 16px; font-weight: 800; margin: 12px 0 4px 0;
    letter-spacing: 1px;
  }
  .stat-box {
    background: #f0f4f8; border-radius: 8px;
    padding: 8px 16px; text-align: center;
    border-left: 4px solid #1565c0;
  }
</style>
""", unsafe_allow_html=True)

# ── Supabase 連接 ────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ── 欄位對應 ────────────────────────────────────────────
COLUMNS_ZH = {
    "status":        "施工順序",
    "completion":    "完成率",
    "materials":     "備料",
    "case_no":       "案號",
    "project_name":  "工程名稱",
    "client":        "業主",
    "tracking":      "追蹤進度",
    "plan_doc":      "施工規劃單",
    "drawing":       "製造圖面",
    "pipe_support":  "管撐製作",
    "welding":       "研磨點焊",
    "nde":           "焊道NDE",
    "sandblast":     "噴砂",
    "assembly":      "組立*",
    "painting":      "噴漆",
    "pressure_test": "試壓",
    "handover":      "交站",
    "handover_year": "年份",
    "est_delivery":  "預計交期",
    "notes":         "備註",
    "contact":       "對應窗口",
    "closed":        "已結案",
}

STATUS_COLOR = {
    "in_progress": "#FFFF99",
    "pending":     "#CCE8FF",
    "not_started": "#FFFFFF",
    "suspended":   "#FFE0B2",
    "completed":   "#F5F5F5",
}

STATUS_LABEL = {
    "製作中": "in_progress",
    "待交站": "pending",
    "製作中(停工)": "suspended",
}

SECTIONS = ["主要工程", "偉鴻", "材料案"]

# ── 讀取資料 ────────────────────────────────────────────
@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    res = supabase.table("projects").select("*").order("id").execute()
    if not res.data:
        return pd.DataFrame(columns=list(COLUMNS_ZH.keys()) + ["id","section","status_type"])
    df = pd.DataFrame(res.data)
    return df

def refresh():
    st.cache_data.clear()
    st.rerun()

# ── 頁面標題 ────────────────────────────────────────────
today = datetime.now().strftime("%Y.%m.%d")
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a1929,#0d47a1);
  padding:14px 20px;border-radius:8px;margin-bottom:12px;">
  <div style="color:#fff;font-size:22px;font-weight:900;letter-spacing:2px;">
    ⚙ 工程案執行進度管理系統
  </div>
  <div style="color:#90caf9;font-size:12px;margin-top:4px;">
    更新日期：{today}
  </div>
</div>
""", unsafe_allow_html=True)

# ── 載入資料 ────────────────────────────────────────────
df_all = load_data()

# ── 統計數字 ────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
counts = df_all["status_type"].value_counts() if not df_all.empty else {}
with c1:
    st.metric("📋 全部", len(df_all))
with c2:
    st.metric("⚙ 製作中", int(counts.get("in_progress", 0)))
with c3:
    st.metric("📦 待交站", int(counts.get("pending", 0)))
with c4:
    st.metric("⏳ 未開始", int(counts.get("not_started", 0)))
with c5:
    st.metric("✅ 已完成", int(counts.get("completed", 0)))

st.divider()

# ── 篩選列 ────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns([2, 1.5, 1.2, 1])
with fc1:
    search = st.text_input("🔍 搜尋", placeholder="案號 / 工程名稱 / 業主 / 窗口", label_visibility="collapsed")
with fc2:
    status_opts = ["全部狀態", "製作中", "待交站", "未開始", "已完成", "停工"]
    filter_status = st.selectbox("狀態", status_opts, label_visibility="collapsed")
with fc3:
    year_opts = ["全部年份", "115", "114", "未填年份"]
    filter_year = st.selectbox("年份", year_opts, label_visibility="collapsed")
with fc4:
    section_opts = ["全部分區"] + SECTIONS
    filter_section = st.selectbox("分區", section_opts, label_visibility="collapsed")

# ── 套用篩選 ────────────────────────────────────────────
STATUS_MAP = {
    "製作中": "in_progress", "待交站": "pending",
    "未開始": "not_started", "已完成": "completed", "停工": "suspended"
}

df_filtered = df_all.copy()
if not df_filtered.empty:
    if search:
        mask = (
            df_filtered["project_name"].str.contains(search, na=False) |
            df_filtered["case_no"].str.contains(search, na=False) |
            df_filtered["client"].str.contains(search, na=False) |
            df_filtered["contact"].str.contains(search, na=False)
        )
        df_filtered = df_filtered[mask]
    if filter_status != "全部狀態":
        df_filtered = df_filtered[df_filtered["status_type"] == STATUS_MAP.get(filter_status, "")]
    if filter_year != "全部年份":
        if filter_year == "未填年份":
            df_filtered = df_filtered[df_filtered["handover_year"].isna() | (df_filtered["handover_year"] == "")]
        else:
            df_filtered = df_filtered[df_filtered["handover_year"] == filter_year]
    if filter_section != "全部分區":
        df_filtered = df_filtered[df_filtered["section"] == filter_section]

st.caption(f"顯示 {len(df_filtered)} / {len(df_all)} 筆")

# ── 顯示各分區表格 ────────────────────────────────────────────
display_cols = list(COLUMNS_ZH.keys())
col_config = {
    "status":        st.column_config.SelectboxColumn("施工順序", options=["製作中","待交站","製作中(停工)",
                      "1月交站","2月交站","預計完成"], width="medium"),
    "completion":    st.column_config.TextColumn("完成率", width="small"),
    "materials":     st.column_config.TextColumn("備料", width="small"),
    "case_no":       st.column_config.TextColumn("案號", width="medium"),
    "project_name":  st.column_config.TextColumn("工程名稱", width="large"),
    "client":        st.column_config.TextColumn("業主", width="small"),
    "tracking":      st.column_config.TextColumn("追蹤進度", width="medium"),
    "plan_doc":      st.column_config.TextColumn("施工規劃單", width="small"),
    "drawing":       st.column_config.TextColumn("製造圖面", width="small"),
    "pipe_support":  st.column_config.TextColumn("管撐製作", width="small"),
    "welding":       st.column_config.TextColumn("研磨點焊", width="medium"),
    "nde":           st.column_config.TextColumn("焊道NDE", width="small"),
    "sandblast":     st.column_config.TextColumn("噴砂", width="small"),
    "assembly":      st.column_config.TextColumn("組立*", width="small"),
    "painting":      st.column_config.TextColumn("噴漆", width="small"),
    "pressure_test": st.column_config.TextColumn("試壓", width="small"),
    "handover":      st.column_config.TextColumn("交站", width="medium"),
    "handover_year": st.column_config.SelectboxColumn("年份", options=["114","115","116",""], width="small"),
    "est_delivery":  st.column_config.TextColumn("預計交期", width="medium"),
    "notes":         st.column_config.TextColumn("備註", width="medium"),
    "contact":       st.column_config.TextColumn("對應窗口", width="small"),
    "closed":        st.column_config.TextColumn("結案", width="small"),
}

sections_to_show = SECTIONS if filter_section == "全部分區" else [filter_section]
edited_data = {}

for sec in sections_to_show:
    df_sec = df_filtered[df_filtered["section"] == sec].copy() if not df_filtered.empty else pd.DataFrame()
    if df_sec.empty and filter_section == "全部分區":
        continue

    in_p = len(df_sec[df_sec["status_type"] == "in_progress"]) if not df_sec.empty else 0
    pend = len(df_sec[df_sec["status_type"] == "pending"]) if not df_sec.empty else 0
    ns   = len(df_sec[df_sec["status_type"] == "not_started"]) if not df_sec.empty else 0
    comp = len(df_sec[df_sec["status_type"] == "completed"]) if not df_sec.empty else 0

    badges = ""
    if in_p: badges += f'<span style="background:#e6c800;color:#000;border-radius:10px;padding:1px 8px;font-size:11px;margin-left:6px;font-weight:700;">製作中 {in_p}</span>'
    if pend: badges += f'<span style="background:#2196f3;color:#fff;border-radius:10px;padding:1px 8px;font-size:11px;margin-left:6px;font-weight:700;">待交站 {pend}</span>'
    if ns:   badges += f'<span style="background:#90a4ae;color:#fff;border-radius:10px;padding:1px 8px;font-size:11px;margin-left:6px;font-weight:700;">未開始 {ns}</span>'
    if comp: badges += f'<span style="background:#757575;color:#fff;border-radius:10px;padding:1px 8px;font-size:11px;margin-left:6px;font-weight:700;">完成 {comp}</span>'

    st.markdown(f"""
    <div class="section-header">
      【{sec}】 共 {len(df_sec)} 筆 {badges}
    </div>
    """, unsafe_allow_html=True)

    if df_sec.empty:
        st.caption("此分區目前沒有資料")
        continue

    show_df = df_sec[display_cols].copy()
    edited = st.data_editor(
        show_df,
        key=f"editor_{sec}",
        column_config=col_config,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        height=min(400, 45 + len(df_sec) * 36),
    )
    edited_data[sec] = (df_sec["id"].tolist(), edited)

# ── 儲存變更 ────────────────────────────────────────────
st.divider()
bc1, bc2, bc3, bc4 = st.columns([1, 1, 1, 3])

with bc1:
    if st.button("💾 儲存變更", type="primary", use_container_width=True):
        try:
            saved = 0
            for sec, (ids, edited_df) in edited_data.items():
                for i, row in edited_df.iterrows():
                    row_dict = row.to_dict()
                    # 自動推斷 status_type
                    s = str(row_dict.get("status", ""))
                    if "製作中" in s and "停工" not in s:
                        row_dict["status_type"] = "in_progress"
                    elif "待交站" in s:
                        row_dict["status_type"] = "pending"
                    elif "停工" in s:
                        row_dict["status_type"] = "suspended"
                    elif "交站" in s or row_dict.get("completion") == "100%":
                        row_dict["status_type"] = "completed"
                    row_dict["section"] = sec
                    row_dict = {k: (v if v is not None else "") for k, v in row_dict.items()}
                    if i < len(ids):
                        supabase.table("projects").update(row_dict).eq("id", ids[i]).execute()
                    else:
                        supabase.table("projects").insert(row_dict).execute()
                    saved += 1
            st.success(f"✅ 已儲存 {saved} 筆！")
            refresh()
        except Exception as e:
            st.error(f"儲存失敗：{e}")

with bc2:
    # 匯出 PDF（使用 fpdf2）
    if st.button("📄 匯出 PDF", use_container_width=True):
        try:
            from fpdf import FPDF
            import tempfile, os

            pdf = FPDF(orientation="L", format="A3")
            pdf.set_auto_page_break(auto=True, margin=10)
            pdf.add_font("NotoSans", "", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc")
            pdf.add_font("NotoSans", "B", "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc")

            headers = ["施工順序","完成率","備料","案號","工程名稱","業主","追蹤進度",
                       "製造圖面","管撐","研磨點焊","NDE","噴砂","組立","噴漆","試壓","交站","年份","備註","窗口"]
            keys    = ["status","completion","materials","case_no","project_name","client","tracking",
                       "drawing","pipe_support","welding","nde","sandblast","assembly","painting",
                       "pressure_test","handover","handover_year","notes","contact"]
            widths  = [20,12,8,22,55,14,30,14,12,20,12,12,12,12,12,16,10,24,12]

            STATUS_RGB = {
                "in_progress":(255,255,153), "pending":(204,232,255),
                "not_started":(255,255,255), "suspended":(255,224,178),
                "completed":(240,240,240),
            }

            for sec in SECTIONS:
                df_sec = df_all[df_all["section"] == sec] if not df_all.empty else pd.DataFrame()
                if df_sec.empty:
                    continue

                pdf.add_page()
                pdf.set_font("NotoSans", "B", 14)
                pdf.set_text_color(10, 35, 80)
                pdf.cell(0, 10, f"【{sec}】 工程案執行進度  ({today})", ln=True)
                pdf.ln(2)

                # 表頭
                pdf.set_font("NotoSans", "B", 7)
                pdf.set_fill_color(29, 71, 157)
                pdf.set_text_color(255, 255, 255)
                for h, w in zip(headers, widths):
                    pdf.cell(w, 7, h, border=1, fill=True, align="C")
                pdf.ln()

                # 資料列
                pdf.set_font("NotoSans", "", 6.5)
                pdf.set_text_color(30, 30, 30)
                for _, row in df_sec.iterrows():
                    rgb = STATUS_RGB.get(row.get("status_type",""), (255,255,255))
                    pdf.set_fill_color(*rgb)
                    for k, w in zip(keys, widths):
                        val = str(row.get(k,"") or "")
                        if len(val) > 20:
                            val = val[:19] + "…"
                        pdf.cell(w, 6, val, border=1, fill=True)
                    pdf.ln()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    pdf_bytes = f.read()
                os.unlink(tmp.name)

            fname = f"工程案執行進度_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button("⬇ 下載 PDF", pdf_bytes, file_name=fname, mime="application/pdf")
        except Exception as e:
            st.error(f"PDF 產生失敗：{e}")

with bc3:
    if st.button("🔄 重新整理", use_container_width=True):
        refresh()

# ── 圖例 ────────────────────────────────────────────────
st.markdown("""
<div style="font-size:12px;color:#888;margin-top:8px;">
  <span style="background:#FFFF99;padding:2px 8px;border-radius:3px;margin-right:8px;">■ 製作中</span>
  <span style="background:#CCE8FF;padding:2px 8px;border-radius:3px;margin-right:8px;">■ 待交站</span>
  <span style="background:#ffffff;border:1px solid #ccc;padding:2px 8px;border-radius:3px;margin-right:8px;">■ 未開始</span>
  <span style="background:#FFE0B2;padding:2px 8px;border-radius:3px;margin-right:8px;">■ 停工</span>
  <span style="background:#F5F5F5;border:1px solid #ccc;padding:2px 8px;border-radius:3px;">■ 已完成</span>
  &nbsp;&nbsp;★ 雙擊儲存格可直接編輯，完成後按「儲存變更」
</div>
""", unsafe_allow_html=True)
