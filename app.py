import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ==========================================================
# 1. 密碼檢查功能 (門神)
# ==========================================================
def check_password():
    """如果密碼正確則返回 True，否則顯示密碼輸入框。"""
    def password_entered():
        """檢查輸入的密碼是否正確。"""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 為了安全，刪除輸入暫存
        else:
            st.session_state["password_correct"] = False

    # 如果已經驗證過，直接返回 True
    if st.session_state.get("password_correct", False):
        return True

    # 顯示密碼輸入介面
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

# 如果密碼不正確，停止後續所有程式碼執行
if not check_password():
    st.stop()

# ==========================================================
# 2. 以下是你原本 100% 原汁原味的系統內容
# ==========================================================

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
    font-size: 12px; align-items: center;
  }
  .color-box {
    width: 13px; height: 13px; border-radius: 3px;
    border: 1px solid #bbb; display: inline-block; vertical-align: middle;
  }
</style>
""", unsafe_allow_html=True)

# ── 連接 ──────────────────────────────────────────────────
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
    # 全面清除 None / nan
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str)
        df[col] = df[col].replace({"None":"","nan":"","NaN":"","none":""})
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

DISPLAY_COLS = [
    "status","completion","materials","case_no","project_name","client",
    "tracking","drawing","pipe_support","welding","nde","sandblast",
    "assembly","painting","pressure_test","handover","handover_year","contact",
]
COL_CONFIG = {
    "status":        st.column_config.TextColumn("施工順序"),
    "completion":    st.column_config.TextColumn("完成率"),
    "materials":     st.column_config.TextColumn("備料"),
    "case_no":       st.column_config.TextColumn("案號"),
    "project_name":  st.column_config.TextColumn("工程名稱", width="large"),
    "client":        st.column_config.TextColumn("業主"),
    "tracking":      st.column_config.TextColumn("備註", width="medium"),
    "drawing":       st.column_config.TextColumn("製造圖面"),
    "pipe_support":  st.column_config.TextColumn("管撐製作"),
    "welding":       st.column_config.TextColumn("研磨點焊"),
    "nde":           st.column_config.TextColumn("焊道NDE"),
    "sandblast":     st.column_config.TextColumn("噴砂"),
    "assembly":      st.column_config.TextColumn("組立*"),
    "painting":      st.column_config.TextColumn("噴漆"),
    "pressure_test": st.column_config.TextColumn("試壓"),
    "handover":      st.column_config.TextColumn("交站"),
    "handover_year": st.column_config.SelectboxColumn("年份", options=["","114","115","116"]),
    "contact":       st.column_config.TextColumn("對應窗口"),
    "status_type":   st.column_config.SelectboxColumn("狀態", options=list(STATUS_CONFIG.keys())),
}

# ── 標題 ──────────────────────────────────────────────────
today = datetime.now().strftime("%Y.%m.%d")
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a1929,#0d47a1);
  padding:14px 20px;border-radius:8px;margin-bottom:12px;">
  <div style="color:#fff;font-size:20px;font-weight:900;letter-spacing:2px;">
    ⚙ 工程案執行進度管理系統
  </div>
  <div style="color:#90caf9;font-size:12px;margin-top:3px;">
    更新日期：{today} ／ Supabase 雲端資料庫 ／ 多人共用
  </div>
</div>
""", unsafe_allow_html=True)

df_all = load_data()

# ── 統計數字 ──────────────────────────────────────────────
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

# ── 頁面切換 ──────────────────────────────────────────────
page_tab1, page_tab2, page_tab3 = st.tabs(["📋 進度管理", "📊 工時分析", "⏱ 生產工時儀表板"])

# ════════════════════════════════════════════════════════
# PAGE 1：進度管理
# ════════════════════════════════════════════════════════
with page_tab1:

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

    for i,(key,cfg) in enumerate(STATUS_CONFIG.items()):
        active = key in st.session_state.active_status
        count = int(df_all["status_type"].value_counts().get(key,0)) if not df_all.empty else 0
        label = f"{cfg['icon']} {cfg['label']} ({count})" + (" ✓" if active else "")
        with btn_cols[i+1]:
            if st.button(label, use_container_width=True,
                         type="primary" if active else "secondary"):
                if active: st.session_state.active_status.discard(key)
                else:      st.session_state.active_status.add(key)
                st.rerun()

    f1,f2,f3 = st.columns([3,1.5,1.5])
    with f1:
        search = st.text_input("🔍", placeholder="搜尋案號 / 工程名稱 / 業主 / 窗口",
                               label_visibility="collapsed")
    with f2:
        filter_year = st.selectbox("年份", ["全部年份","115","114","未填年份"],
                                   label_visibility="collapsed")
    with f3:
        filter_section = st.selectbox("分區", ["全部分區"]+SECTIONS,
                                      label_visibility="collapsed")

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
            mask = (df["project_name"].str.contains(search,na=False) |
                    df["case_no"].str.contains(search,na=False) |
                    df["client"].str.contains(search,na=False) |
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
                    badges += (f'<span style="background:{cfg["btn"]};color:{cfg["text"]};'
                               f'border-radius:10px;padding:1px 9px;font-size:11px;'
                               f'margin-left:6px;font-weight:700;">{cfg["label"]} {n}</span>')

        st.markdown(f'<div class="section-header">【{sec}】 共 {len(df_sec)} 筆 {badges}</div>',
                    unsafe_allow_html=True)

        if df_sec.empty:
            st.caption("此分區目前沒有資料")
            continue

        show_df = df_sec[[c for c in DISPLAY_COLS if c in df_sec.columns]].copy()
        styled = (show_df.assign(status_type=df_sec["status_type"].values)
                  .style.apply(color_rows,axis=1).format(na_rep=""))
        st.dataframe(styled, use_container_width=True, hide_index=True,
                     height=min(420,38+len(df_sec)*35),
                     column_config={k:v for k,v in COL_CONFIG.items() if k in show_df.columns})

        with st.expander(f"✏️ 編輯【{sec}】"):
            edit_df = df_sec[[c for c in DISPLAY_COLS+["status_type"] if c in df_sec.columns]].copy()
            edited = st.data_editor(edit_df, key=f"edit_{sec}",
                                    column_config=COL_CONFIG,
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
                        row_dict = {k:("" if (v is None or str(v) in ["None","nan","NaN",""]) else str(v))
                                    for k,v in row.items()}
                        row_dict["section"] = sec
                        if not row_dict.get("status_type"):
                            s = row_dict.get("status","")
                            if "製作中" in s and "停工" not in s: row_dict["status_type"]="in_progress"
                            elif "待交站" in s: row_dict["status_type"]="pending"
                            elif "停工" in s:  row_dict["status_type"]="suspended"
                            elif "交站" in s or row_dict.get("completion")=="100%":
                                row_dict["status_type"]="completed"
                                
                        # ── 【新增：自動記錄開始日期】 ──
                        if row_dict.get("status_type") == "in_progress":
                            if i < len(ids):
                                old_row = df_all[df_all["id"] == str(ids[i])]
                                old_status = old_row["status_type"].values[0] if not old_row.empty else ""
                                if old_status != "in_progress":
                                    row_dict["started_at"] = datetime.now().strftime("%Y-%m-%d")
                            else:
                                row_dict["started_at"] = datetime.now().strftime("%Y-%m-%d")
                        # ────────────────────────────
                                
                        if i < len(ids):
                            supabase.table("projects").update(row_dict).eq("id",ids[i]).execute()
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

    with st.expander("📄 匯出 PDF"):
        if st.button("產生 PDF"):
            try:
                from fpdf import FPDF
                import tempfile, os, urllib.request

                # ── 取得中文字型 ──────────────────────────
                font_path = "/tmp/NotoSansSC.ttf"
                if not os.path.exists(font_path):
                    with st.spinner("首次使用：下載中文字型中（約5秒）..."):
                        urllib.request.urlretrieve(
                            "https://github.com/googlefonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf",
                            font_path
                        )

                pdf = FPDF(orientation="L", format="A3")
                pdf.set_auto_page_break(auto=True, margin=10)
                pdf.add_font("Chinese", "", font_path)
                pdf.add_font("Chinese", "B", font_path)

                HEADERS=["施工順序","完成率","備料","案號","工程名稱","業主",
                         "備註","製造圖面","管撐","研磨點焊","NDE","噴砂",
                         "組立","噴漆","試壓","交站","年份","窗口"]
                KEYS=["status","completion","materials","case_no","project_name","client",
                      "tracking","drawing","pipe_support","welding","nde","sandblast",
                      "assembly","painting","pressure_test","handover","handover_year","contact"]
                WIDTHS=[20,11,7,22,55,13,30,13,11,18,11,11,11,11,11,15,9,13]
                PDF_BG={"in_progress":(255,255,153),"pending":(204,232,255),
                        "not_started":(255,255,255),"suspended":(255,224,178),"completed":(240,240,240)}

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
                    for h,w in zip(HEADERS,WIDTHS):
                        pdf.cell(w,7,h,border=1,fill=True,align="C")
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
                fname = f"工程案執行進度_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button("⬇ 下載 PDF", pdf_bytes, file_name=fname, mime="application/pdf")
            except Exception as e:
                st.error(f"PDF 失敗：{e}")

# ════════════════════════════════════════════════════════
# PAGE 2：工時分析
# ════════════════════════════════════════════════════════
with page_tab2:
    if df_all.empty:
        st.warning("尚無資料")
    else:
        st.markdown("### 📊 工時分析")

        # ── 分析篩選 ──────────────────────────────────────
        a1,a2 = st.columns([2,2])
        with a1:
            sec_filter = st.selectbox("分區", ["全部"]+SECTIONS, key="ana_sec")
        with a2:
            year_filter = st.selectbox("年份", ["全部","115","114"], key="ana_year")

        df_ana = df_all.copy()
        if sec_filter != "全部":
            df_ana = df_ana[df_ana["section"]==sec_filter]
        if year_filter != "全部":
            df_ana = df_ana[df_ana["handover_year"]==year_filter]

        if df_ana.empty:
            st.info("此條件下沒有資料")
        else:
            st.caption(f"分析範圍：{len(df_ana)} 筆")
            st.divider()

            # ── 1. 各狀態分佈圓餅圖 ──────────────────────
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("#### 🔵 各狀態分佈")
                status_counts = df_ana["status_type"].value_counts().reset_index()
                status_counts.columns = ["status_type","數量"]
                status_counts["狀態"] = status_counts["status_type"].map(
                    {k:v["label"] for k,v in STATUS_CONFIG.items()})
                st.bar_chart(
                    status_counts.set_index("狀態")["數量"],
                    color="#2196f3", use_container_width=True
                )

            # ── 2. 完成率分佈 ──────────────────────────────
            with c2:
                st.markdown("#### 📈 完成率分佈")
                def parse_pct(s):
                    try: return float(str(s).replace("%","").strip())
                    except: return None
                df_ana["_pct"] = df_ana["completion"].apply(parse_pct)
                df_pct = df_ana[df_ana["_pct"].notna()].copy()
                if not df_pct.empty:
                    bins = [0,25,50,75,100]
                    labels = ["0-25%","26-50%","51-75%","76-100%"]
                    df_pct["區間"] = pd.cut(df_pct["_pct"], bins=bins, labels=labels, include_lowest=True)
                    dist = df_pct["區間"].value_counts().sort_index().reset_index()
                    dist.columns = ["區間","數量"]
                    st.bar_chart(dist.set_index("區間")["數量"],
                                 color="#4caf50", use_container_width=True)
                else:
                    st.info("無完成率資料")

            st.divider()

            # ── 3. 各工序完成數量長條圖 ────────────────────
            st.markdown("#### 🔧 各工序完成數量")
            st.caption("有填入日期/資料 = 該工序已完成")

            process_done = {}
            for col, name in zip(PROCESS_COLS, PROCESS_NAMES):
                if col in df_ana.columns:
                    done = df_ana[col].apply(lambda x: 1 if str(x).strip() not in ["","None","nan","-"] else 0).sum()
                    process_done[name] = int(done)

            df_proc = pd.DataFrame(list(process_done.items()), columns=["工序","完成數量"])
            df_proc["未完成"] = len(df_ana) - df_proc["完成數量"]
            st.bar_chart(df_proc.set_index("工序")[["完成數量","未完成"]],
                         use_container_width=True)

            st.divider()

            # ── 4. 各業主工程數量 ──────────────────────────
            c3,c4 = st.columns(2)
            with c3:
                st.markdown("#### 🏢 各業主工程數量")
                client_cnt = df_ana[df_ana["client"]!=""]["client"].value_counts().head(10)
                if not client_cnt.empty:
                    st.bar_chart(client_cnt, color="#ff7043", use_container_width=True)
                else:
                    st.info("無業主資料")

            # ── 5. 各分區完成率平均 ────────────────────────
            with c4:
                st.markdown("#### 📦 各分區平均完成率")
                df_ana["_pct2"] = df_ana["completion"].apply(parse_pct)
                sec_avg = df_ana.groupby("section")["_pct2"].mean().dropna().round(1)
                if not sec_avg.empty:
                    df_avg = sec_avg.reset_index()
                    df_avg.columns = ["分區","平均完成率(%)"]
                    st.bar_chart(df_avg.set_index("分區")["平均完成率(%)"],
                                 color="#9c27b0", use_container_width=True)
                else:
                    st.info("無完成率資料")

            st.divider()

            # ── 6. 製作中工程完成率排行 ────────────────────
            st.markdown("#### ⚙ 製作中工程 — 完成率排行")
            df_inprog = df_ana[df_ana["status_type"]=="in_progress"].copy()
            df_inprog["_pct3"] = df_inprog["completion"].apply(parse_pct)
            df_inprog = df_inprog[df_inprog["_pct3"].notna()].sort_values("_pct3", ascending=False)

            if df_inprog.empty:
                st.info("目前沒有製作中的工程")
            else:
                show_cols = ["project_name","client","section","completion","tracking"]
                show_names = {"project_name":"工程名稱","client":"業主",
                              "section":"分區","completion":"完成率","tracking":"備註"}
                disp = df_inprog[[c for c in show_cols if c in df_inprog.columns]].rename(columns=show_names)
                st.dataframe(disp, use_container_width=True, hide_index=True)

            st.divider()

            # ── 7. 待交站工程清單 ──────────────────────────
            st.markdown("#### 📦 待交站工程清單")
            df_pending = df_ana[df_ana["status_type"]=="pending"].copy()
            if df_pending.empty:
                st.info("目前沒有待交站的工程")
            else:
                show_cols2 = ["project_name","client","section","handover","handover_year","contact"]
                show_names2 = {"project_name":"工程名稱","client":"業主","section":"分區",
                               "handover":"交站","handover_year":"年份","contact":"對應窗口"}
                disp2 = df_pending[[c for c in show_cols2 if c in df_pending.columns]].rename(columns=show_names2)
                st.dataframe(disp2, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════
# PAGE 3：生產工時儀表板
# ════════════════════════════════════════════════════════
with page_tab3:
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        PLOTLY_OK = True
    except ImportError:
        PLOTLY_OK = False
        st.error("請在 requirements.txt 加入 plotly，重新部署後再使用。")

    if PLOTLY_OK:

        # ── 中文字型設定 ───────────────────────────────────
        FONT = "Microsoft JhengHei, PingFang TC, Heiti TC, sans-serif"

        def apply_font(fig):
            fig.update_layout(
                font=dict(family=FONT, size=13),
                title_font=dict(family=FONT, size=15),
                legend=dict(font=dict(family=FONT)),
                paper_bgcolor="white", plot_bgcolor="#f8faff",
            )
            return fig

        # ── 讀取 work_logs ─────────────────────────────────
        @st.cache_data(ttl=30)
        def load_work_logs() -> pd.DataFrame:
            try:
                res = supabase.table("work_logs").select("*").order("start_time", desc=True).execute()
                if not res.data:
                    return pd.DataFrame()
                df = pd.DataFrame(res.data)
                df["start_time"]  = pd.to_datetime(df["start_time"],  errors="coerce")
                df["end_time"]    = pd.to_datetime(df["end_time"],    errors="coerce")
                df["actual_hours"]   = pd.to_numeric(df["actual_hours"],   errors="coerce")
                df["standard_hours"] = pd.to_numeric(df["standard_hours"], errors="coerce")
                df = df.dropna(subset=["start_time"])
                return df
            except Exception as e:
                return pd.DataFrame()

        # ── 頁面標題 ───────────────────────────────────────
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0a2540,#1a6b3c);
          padding:12px 20px;border-radius:8px;margin-bottom:14px;">
          <div style="color:#fff;font-size:18px;font-weight:900;letter-spacing:2px;">
            ⏱ 生產工時分析儀表板
          </div>
          <div style="color:#a8d5b5;font-size:12px;margin-top:3px;">
            資料來源：work_logs 資料表 ／ 即時同步
          </div>
        </div>
        """, unsafe_allow_html=True)

        df_wl = load_work_logs()

        # ── 資料表不存在或無資料 ──────────────────────────
        if df_wl.empty:
            st.warning("⚠️ 尚無工時資料，或 `work_logs` 資料表尚未建立。")
            st.markdown("#### 📋 請先在 Supabase SQL Editor 執行以下語法建立資料表：")
            st.code("""
CREATE TABLE work_logs (
  id            bigint generated always as identity primary key,
  order_no      text,           -- 工單編號
  process_name  text,           -- 工序名稱（焊接/組立/噴漆...）
  operator      text,           -- 執行人員
  start_time    timestamptz,    -- 開始時間
  end_time      timestamptz,    -- 結束時間
  actual_hours  numeric,        -- 實際工時（小時）
  standard_hours numeric,       -- 標準工時（小時）
  notes         text,           -- 備註
  created_at    timestamptz default now()
);

-- 範例測試資料（可選）
INSERT INTO work_logs (order_no, process_name, operator, start_time, end_time, actual_hours, standard_hours) VALUES
('WO-001', '焊接',  '張三', '2026-02-20 08:00', '2026-02-20 12:00', 4.0, 3.5),
('WO-001', '組立',  '李四', '2026-02-20 13:00', '2026-02-20 17:00', 4.0, 4.0),
('WO-002', '噴漆',  '王五', '2026-02-21 08:00', '2026-02-21 11:30', 3.5, 2.5),
('WO-002', '焊接',  '張三', '2026-02-21 13:00', '2026-02-21 18:00', 5.0, 4.0),
('WO-003', '研磨',  '李四', '2026-02-22 08:00', '2026-02-22 10:00', 2.0, 2.0),
('WO-003', '試壓',  '王五', '2026-02-22 10:30', '2026-02-22 12:00', 1.5, 1.5),
('WO-004', '組立',  '趙六', '2026-02-24 08:00', '2026-02-24 14:00', 6.0, 4.5),
('WO-004', '焊接',  '張三', '2026-02-24 14:30', '2026-02-24 18:00', 3.5, 3.0),
('WO-005', '噴漆',  '李四', '2026-02-25 08:00', '2026-02-25 09:30', 1.5, 2.0),
('WO-005', '組立',  '趙六', '2026-02-25 10:00', '2026-02-25 16:00', 6.0, 5.0);
            """, language="sql")
            st.info("建立資料表並插入資料後，重新整理頁面即可看到分析結果。")
            st.stop()

        # ── 日期篩選器 ─────────────────────────────────────
        st.markdown("#### 📅 查詢區間")
        d1, d2, d3, d4 = st.columns([1.5, 1.5, 1.5, 1.5])
        min_date = df_wl["start_time"].dt.date.min()
        max_date = df_wl["start_time"].dt.date.max()
        with d1:
            date_from = st.date_input("開始日期", value=min_date, min_value=min_date, max_value=max_date)
        with d2:
            date_to   = st.date_input("結束日期", value=max_date, min_value=min_date, max_value=max_date)
        with d3:
            op_list = ["全部人員"] + sorted(df_wl["operator"].dropna().unique().tolist())
            sel_op = st.selectbox("人員", op_list)
        with d4:
            proc_list =
