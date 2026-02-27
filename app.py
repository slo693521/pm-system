import re
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta

# ==========================================
# 密碼檢查
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
# 系統主程式
# ==========================================
st.set_page_config(page_title="工程案執行進度管理系統",
                   page_icon="⚙", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  /* ══ 基礎 ══ */
  .block-container { padding-top: 0.3rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
  header[data-testid="stHeader"] { background: transparent; }

  /* ══ 自訂統計卡（HTML，完全控制顏色）══ */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px; margin-bottom: 10px;
  }
  .kpi-card {
    background: #1a3a5c; border-radius: 10px;
    padding: 10px 8px; text-align: center;
    border: 1px solid #2a5080;
  }
  .kpi-label { color: #90caf9; font-size: 12px; font-weight: 700; margin-bottom: 2px; }
  .kpi-value { color: #ffffff; font-size: 1.6rem; font-weight: 900; line-height: 1.1; }

  /* ══ 分區標題 ══ */
  .section-header {
    background: linear-gradient(90deg, #0d2137, #1a3a5c); color: #fff;
    padding: 10px 14px; border-radius: 8px;
    font-size: 15px; font-weight: 800; margin: 12px 0 6px 0; letter-spacing: 1px;
  }

  /* ══ 狀態篩選按鈕 ══ */
  .stButton > button {
    border-radius: 18px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    min-height: 42px !important;
    color: #111 !important;
    padding: 4px 6px !important;
  }

  /* ══ 圖例列 ══ */
  .legend-bar {
    display: flex; gap: 8px; flex-wrap: wrap;
    background: #1e3a5f; padding: 8px 12px; border-radius: 8px;
    margin-bottom: 8px; font-size: 12px; font-weight: 600;
    color: #e3f0ff; align-items: center; border: 1px solid #2a5080;
  }
  .color-box {
    width: 13px; height: 13px; border-radius: 3px;
    border: 1px solid #888; display: inline-block; vertical-align: middle;
  }

  /* ══ 工程卡片（手機用）══ */
  .project-card {
    background: #fff; border-radius: 10px; padding: 12px 14px;
    margin-bottom: 8px; border-left: 5px solid #1a3a5c;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12);
  }
  .project-card.status-in_progress  { border-left-color: #e6c800; background: #fffff0; }
  .project-card.status-pending       { border-left-color: #2196f3; background: #e8f4ff; }
  .project-card.status-not_started   { border-left-color: #90a4ae; background: #fafafa; }
  .project-card.status-suspended     { border-left-color: #ff7043; background: #fff3ee; }
  .project-card.status-completed     { border-left-color: #757575; background: #f5f5f5; }
  .card-title { font-size: 15px; font-weight: 800; color: #0d2137; margin-bottom: 4px; }
  .card-sub   { font-size: 12px; color: #444; margin: 2px 0; }
  .card-badge {
    display: inline-block; border-radius: 12px; padding: 2px 10px;
    font-size: 11px; font-weight: 700; margin: 4px 4px 0 0;
  }
  .card-red { color: #c62828; font-weight: 900; }

  /* ══ dataframe 字色 ══ */
  [data-testid="stDataFrame"] td { color: #111 !important; font-size: 13px !important; }
  [data-testid="stDataFrame"] th { color: #fff !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ── 連接 ──────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ── UI 狀態持久化（存到 Supabase user_prefs）──────────
import json as _json

def load_ui_state() -> dict:
    """從 Supabase 讀取上次 UI 狀態"""
    try:
        res = supabase.table("user_prefs").select("value").eq("key","ui_state").execute()
        if res.data:
            return _json.loads(res.data[0]["value"])
    except: pass
    return {}

def save_ui_state(state: dict):
    """把目前 UI 狀態存回 Supabase"""
    try:
        supabase.table("user_prefs").upsert(
            {"key": "ui_state", "value": _json.dumps(state, ensure_ascii=False)}
        ).execute()
    except: pass

@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    res = supabase.table("projects").select("*").order("case_no", desc=True).execute()
    if not res.data: return pd.DataFrame()
    df = pd.DataFrame(res.data)
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).replace({"None":"","nan":"","NaN":"","none":""})
    # 固定顯示順序欄（新增的排最上面 = 序號最小）
    df.insert(0, "_order", range(1, len(df)+1))
    return df

def refresh():
    st.cache_data.clear()
    st.rerun()

# ── 狀態設定（中英文對照）──────────────────────────────────
STATUS_CONFIG = {
    "in_progress": {"label":"製作中","icon":"⚙", "bg":"#FFFF99","btn":"#e6c800","text":"#000"},
    "pending":     {"label":"待交站","icon":"📦","bg":"#CCE8FF","btn":"#2196f3","text":"#fff"},
    "not_started": {"label":"未開始","icon":"⏳","bg":"#FFFFFF","btn":"#90a4ae","text":"#fff"},
    "suspended":   {"label":"停工",  "icon":"⏸","bg":"#FFE0B2","btn":"#ff7043","text":"#fff"},
    "completed":   {"label":"已交站","icon":"✅","bg":"#F0F0F0","btn":"#757575","text":"#fff"},
}
# 中文標籤 ↔ 英文 key 對照
STATUS_ZH_TO_KEY = {v["label"]: k for k, v in STATUS_CONFIG.items()}
STATUS_KEY_TO_ZH = {k: v["label"] for k, v in STATUS_CONFIG.items()}
STATUS_ZH_OPTIONS = [""] + [v["label"] for v in STATUS_CONFIG.values()]

SECTIONS = ["主要工程", "偉鴻", "材料案"]
PROCESS_COLS  = ["drawing","pipe_support","welding","nde","sandblast","assembly","painting","pressure_test","handover"]
PROCESS_NAMES = ["製造圖面","管撐製作","點焊","焊道NDE","噴砂","組立*","噴漆","試壓","交站"]
DISPLAY_COLS  = ["status","completion","materials","case_no","project_name","client",
                 "tracking","drawing","pipe_support","welding","nde","sandblast",
                 "assembly","painting","pressure_test","handover","handover_year","contact"]

# ── 欄位設定（status_type 改為中文下拉）──────────────────
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
    "welding":       st.column_config.TextColumn("點焊"),
    "nde":           st.column_config.TextColumn("焊道NDE"),
    "sandblast":     st.column_config.TextColumn("噴砂"),
    "assembly":      st.column_config.TextColumn("組立*"),
    "painting":      st.column_config.TextColumn("噴漆"),
    "pressure_test": st.column_config.TextColumn("試壓"),
    "handover":      st.column_config.TextColumn("交站"),
    "handover_year": st.column_config.SelectboxColumn("年份", options=["","114","115","116"]),
    "contact":       st.column_config.TextColumn("對應窗口"),
    # ✅ 改為中文下拉選單，直接看得懂
    "status_zh":     st.column_config.SelectboxColumn(
                         "🎨 狀態",
                         options=STATUS_ZH_OPTIONS,
                         help="選擇狀態後列顏色立即更新"),
}

# ── 本週判斷 ──────────────────────────────────────────────
def _week_start():
    now = datetime.now()
    ws  = now - timedelta(days=now.weekday())
    return ws.replace(hour=0, minute=0, second=0, microsecond=0)

def is_this_week(dt_str: str) -> bool:
    """判斷 ISO 日期字串是否在本週內（供 updated_at 使用）"""
    try:
        if not dt_str or dt_str in ("", "None", "nan"): return False
        dt = pd.to_datetime(dt_str, errors="coerce")
        if pd.isna(dt): return False
        ws = _week_start()
        we = ws + timedelta(days=7)
        d  = dt.replace(tzinfo=None)
        return ws <= d < we
    except: return False

def is_this_week_str(raw: str) -> bool:
    """支援 M/D 及 YYYY-MM-DD 格式，判斷是否本週（含週一到週日）"""
    try:
        raw = raw.strip()
        if not raw: return False
        ws = _week_start()
        we = ws + timedelta(days=7)
        if re.match(r"^\d{1,2}/\d{1,2}$", raw):
            year = datetime.now().year
            dt = datetime.strptime(f"{year}/{raw}", "%Y/%m/%d")
        else:
            dt = pd.to_datetime(raw, errors="coerce")
            if pd.isna(dt): return False
            dt = dt.to_pydatetime()
        return ws <= dt.replace(tzinfo=None) < we
    except: return False

# ── 自動儲存函式 ──────────────────────────────────────────
def do_save(sec: str, original_df: pd.DataFrame, editor_state) -> int:
    """
    處理 data_editor 的 session_state 格式：
    {"edited_rows": {str(row_idx): {col: val}},
     "added_rows":  [{col: val}],
     "deleted_rows":[row_idx]}
    """
    if not isinstance(editor_state, dict):
        return 0
    saved = 0
    now_iso = datetime.now().isoformat()

    # 不送進 Supabase 的前端欄位（id 單獨處理，不放這裡）
    NON_DB_COLS = {"🗑 刪除", "status_zh", "_order"}

    def clean_val(v) -> str:
        """任何值轉乾淨字串，None/nan → 空字串"""
        if v is None: return ""
        if not isinstance(v, str):
            try:
                if pd.isna(v): return ""
            except: pass
        return "" if str(v) in ("None","nan","NaN","none") else str(v)

    def build_row_dict(base_row: pd.Series, changes: dict) -> dict:
        """合併原始列與本次變動，回傳可直接 upsert 的 dict"""
        merged = base_row.to_dict()
        merged.update(changes)
        row_dict = {}
        for k, v in merged.items():
            if k in NON_DB_COLS or k == "id": continue   # id 另外處理
            row_dict[k] = clean_val(v)
        row_dict["section"]    = sec
        row_dict["updated_at"] = now_iso
        # 中文狀態下拉 → 英文 status_type（changes 裡的 status_zh 優先）
        zh_label = clean_val(changes.get("status_zh", merged.get("status_zh","")))
        if zh_label in STATUS_ZH_TO_KEY:
            row_dict["status_type"] = STATUS_ZH_TO_KEY[zh_label]
        # 備援推斷（status_type 仍然空）
        if not row_dict.get("status_type"):
            s = row_dict.get("status","")
            if "製作中" in s and "停工" not in s: row_dict["status_type"] = "in_progress"
            elif "待交站" in s: row_dict["status_type"] = "pending"
            elif "停工" in s:  row_dict["status_type"] = "suspended"
            elif "已交站" in s or "交站" in s or row_dict.get("completion") == "100%": row_dict["status_type"] = "completed"
            else: row_dict["status_type"] = "not_started"

        # ── 自動計算完成率 ────────────────────────────────────
        # 規則：依「目前已填的最高工序」決定完成率，刪除日期時同步降低
        # 製造圖面(drawing) 不計入完成率

        def filled(col): return bool(row_dict.get(col,"").strip())

        # 由低到高依序評估，最後符合的工序決定基準完成率
        # drawing 跳過，不影響百分比
        auto_pct = 0   # 預設 0%，讓刪光所有工序可退回 0

        if filled("pipe_support"):  auto_pct = 20
        if filled("welding"):       auto_pct = 30
        if filled("nde"):           auto_pct = 40
        if filled("sandblast"):     auto_pct = 50

        # 組立（60-80%）：填了就至少 60%，若手動在 60-80 之間則保留手動值
        if filled("assembly"):
            cur_pct_str = row_dict.get("completion","").replace("%","").strip()
            try:   cur_pct = int(float(cur_pct_str))
            except: cur_pct = 0
            if 60 <= cur_pct <= 80:
                auto_pct = cur_pct   # 保留手動值
            else:
                auto_pct = 60        # 至少跳到 60%

        # 噴漆/試壓（85-90%）：填了就至少 85%，手動在 85-90 之間保留
        if filled("painting") or filled("pressure_test"):
            cur_pct_str = row_dict.get("completion","").replace("%","").strip()
            try:   cur_pct = int(float(cur_pct_str))
            except: cur_pct = 0
            if 85 <= cur_pct <= 90:
                auto_pct = cur_pct   # 保留手動值
            else:
                auto_pct = 85

        # 狀態為「待交站」→ 至少 95%
        if row_dict.get("status_type") == "pending":
            if auto_pct < 95:
                auto_pct = 95

        # 狀態為「已交站」→ 100%
        if row_dict.get("status_type") == "completed":
            auto_pct = 100

        # 直接覆蓋（刪除日期時也會往下調整）
        row_dict["completion"] = f"{auto_pct}%" if auto_pct > 0 else ""

        return row_dict

    # 1. 修改的列
    for row_idx, changes in editor_state.get("edited_rows", {}).items():
        try:
            idx = int(row_idx)
            if idx >= len(original_df): continue
            base       = original_df.iloc[idx]
            record_id  = clean_val(base.get("id",""))   # ← 直接從原始列取 id
            if not record_id or record_id in ("","None"): continue
            row_dict = build_row_dict(base, changes)
            supabase.table("projects").update(row_dict).eq("id", record_id).execute()
            saved += 1
        except Exception as e:
            st.toast(f"⚠️ 更新失敗 row {row_idx}：{e}", icon="❌")

    # 2. 新增的列
    for new_row in editor_state.get("added_rows", []):
        try:
            empty    = pd.Series({c: "" for c in original_df.columns})
            row_dict = build_row_dict(empty, new_row)
            row_dict.pop("id", None)
            supabase.table("projects").insert(row_dict).execute()
            saved += 1
        except Exception as e:
            st.toast(f"⚠️ 新增失敗：{e}", icon="❌")

    # 3. 刪除列（勾選🗑後由編輯區按鈕處理，這裡處理 data_editor 內建刪除）
    for row_idx in editor_state.get("deleted_rows", []):
        try:
            idx       = int(row_idx)
            record_id = clean_val(original_df.iloc[idx].get("id","")) if idx < len(original_df) else ""
            if record_id and record_id not in ("","None"):
                supabase.table("projects").delete().eq("id", record_id).execute()
                saved += 1
        except Exception as e:
            st.toast(f"⚠️ 刪除失敗 row {row_idx}：{e}", icon="❌")

    return saved

# ── 標題 ──────────────────────────────────────────────────
today = datetime.now().strftime("%Y.%m.%d")
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a1929,#0d47a1);
  padding:14px 20px;border-radius:8px;margin-bottom:12px;">
  <div style="color:#fff;font-size:20px;font-weight:900;letter-spacing:2px;">⚙ 工程案執行進度管理系統</div>
  <div style="color:#90caf9;font-size:12px;margin-top:3px;">
    更新日期：{today} ／ Supabase 雲端資料庫 ／ 多人共用
  </div>
</div>
""", unsafe_allow_html=True)

df_all = load_data()

if not df_all.empty:
    cts = df_all["status_type"].value_counts()
    kpi_items = [
        ("📋 全部",      len(df_all)),
        ("⚙ 製作中",    int(cts.get("in_progress",0))),
        ("📦 待交站",   int(cts.get("pending",0))),
        ("⏳ 未開始",   int(cts.get("not_started",0))),
        ("⏸ 停工",     int(cts.get("suspended",0))),
        ("✅ 已完成",   int(cts.get("completed",0))),
    ]
    cards_html = "<div class='kpi-grid'>"
    for label, val in kpi_items:
        cards_html += f"""<div class='kpi-card'>
          <div class='kpi-label'>{label}</div>
          <div class='kpi-value'>{val}</div>
        </div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

st.divider()
page_tab1, page_tab2, page_tab3 = st.tabs(["📋 進度管理", "📊 工時分析", "⏱ 生產工時儀表板"])

# ═══════════════════════════════════════════════════════
# PAGE 1：進度管理
# ═══════════════════════════════════════════════════════
with page_tab1:

    # 第一次載入：從 Supabase 還原上次的篩選狀態
    if "ui_loaded" not in st.session_state:
        _saved = load_ui_state()
        st.session_state.active_status  = set(_saved.get("active_status", []))
        st.session_state.filter_year    = _saved.get("filter_year", "全部年份")
        st.session_state.filter_section = _saved.get("filter_section", "全部分區")
        st.session_state.ui_loaded      = True

    if "active_status" not in st.session_state:
        st.session_state.active_status = set()

    st.markdown("**狀態篩選**（可多選）")
    # 手機：3欄 2行；桌機：6欄 1行
    btn_row1 = st.columns(3)
    btn_row2 = st.columns(3)
    all_btns = btn_row1 + btn_row2   # 共 6 格

    with all_btns[0]:
        is_all = not st.session_state.active_status
        if st.button("📋 全部" + (" ✓" if is_all else ""),
                     use_container_width=True,
                     type="primary" if is_all else "secondary"):
            st.session_state.active_status = set()
            save_ui_state({"active_status": [], "filter_year": st.session_state.get("filter_year","全部年份"), "filter_section": st.session_state.get("filter_section","全部分區")})
            st.rerun()
    for i,(key,cfg) in enumerate(STATUS_CONFIG.items()):
        active = key in st.session_state.active_status
        count  = int(df_all["status_type"].value_counts().get(key,0)) if not df_all.empty else 0
        with all_btns[i+1]:
            if st.button(f"{cfg['icon']} {cfg['label']} ({count})" + (" ✓" if active else ""),
                         use_container_width=True,
                         type="primary" if active else "secondary"):
                if active: st.session_state.active_status.discard(key)
                else:      st.session_state.active_status.add(key)
                save_ui_state({"active_status": list(st.session_state.active_status), "filter_year": st.session_state.get("filter_year","全部年份"), "filter_section": st.session_state.get("filter_section","全部分區")})
                st.rerun()

    search = st.text_input("🔍 搜尋", placeholder="案號 / 工程名稱 / 業主 / 窗口", label_visibility="collapsed")
    ff1, ff2 = st.columns(2)
    with ff1:
        filter_year = st.selectbox("年份", ["全部年份","116","115","114","未填年份"],
                                   index=["全部年份","116","115","114","未填年份"].index(
                                       st.session_state.get("filter_year","全部年份")),
                                   label_visibility="collapsed", key="filter_year")
    with ff2:
        filter_section = st.selectbox("分區", ["全部分區"]+SECTIONS,
                                      index=(["全部分區"]+SECTIONS).index(
                                          st.session_state.get("filter_section","全部分區")),
                                      label_visibility="collapsed", key="filter_section")
    # 年份/分區變動時存到雲端
    _cur_ui = {"active_status": list(st.session_state.active_status),
               "filter_year": filter_year, "filter_section": filter_section}
    if st.session_state.get("_last_ui") != _cur_ui:
        save_ui_state(_cur_ui)
        st.session_state["_last_ui"] = _cur_ui

    st.markdown("""
    <div class="legend-bar">
      <strong>顏色：</strong>
      <span><span class="color-box" style="background:#FFFF99"></span> 製作中</span>
      <span><span class="color-box" style="background:#CCE8FF"></span> 待交站</span>
      <span><span class="color-box" style="background:#FFFFFF"></span> 未開始</span>
      <span><span class="color-box" style="background:#FFE0B2"></span> 停工</span>
      <span><span class="color-box" style="background:#F0F0F0"></span> 已完成</span>
      <span style="color:#c62828;font-weight:900">🔴 本週日期</span>
      <span style="margin-left:auto;color:#999;font-size:11px;">★ 展開「✏️ 編輯」→ 改完即自動儲存</span>
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

    # 日期欄若含本週日期 → 紅字加粗（逐欄 applymap）
    DATE_COLS = {"drawing","pipe_support","welding","nde","sandblast",
                 "assembly","painting","pressure_test","handover","tracking",
                 "materials","contact","status","completion"}

    def color_rows(row):
        """整列底色 = 狀態顏色"""
        bg = STATUS_CONFIG.get(row.get("status_type",""),{}).get("bg","#FFFFFF")
        return [f"background-color:{bg}" for _ in row]

    def cell_has_week_date(val: str) -> bool:
        """格子內容是否含本週日期（支援 2/1、2/26、2026-02-26 等格式）"""
        import re as _re
        val = str(val)
        # 找出所有 M/D 或 YYYY-MM-DD 片段
        hits = _re.findall(r"(?<![\d])(\d{1,2}/\d{1,2})(?![\d])", val)
        hits += _re.findall(r"(\d{4}-\d{2}-\d{2})", val)
        for raw in hits:
            if is_this_week_str(raw):
                return True
        return False

    def highlight_col(col):
        """逐欄呼叫：是日期欄才檢查，其他欄直接回傳空字串"""
        if col.name not in DATE_COLS:
            return [""] * len(col)
        return [
            "color:#c62828;font-weight:900" if cell_has_week_date(v) else ""
            for v in col
        ]

    sections_to_show = SECTIONS if filter_section=="全部分區" else [filter_section]

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
            # 本週更新數量
            if "updated_at" in df_sec.columns:
                nw = int(df_sec["updated_at"].apply(lambda x: is_this_week(str(x))).sum())
                if nw:
                    badges += (f'<span style="background:#e53935;color:#fff;border-radius:10px;'
                               f'padding:1px 9px;font-size:11px;margin-left:6px;font-weight:700;">'
                               f'🔴 本週更新 {nw}</span>')

        st.markdown(f'<div class="section-header">【{sec}】 共 {len(df_sec)} 筆 {badges}</div>',
                    unsafe_allow_html=True)
        if df_sec.empty:
            st.caption("此分區目前沒有資料"); continue

        # ── 唯讀顯示（有顏色）──────────────────────────────
        show_cols = [c for c in DISPLAY_COLS if c in df_sec.columns and c != "_order"]
        show_df   = df_sec[show_cols].copy()

        # 加入 updated_at / status_type 讓 color_rows 能讀到
        styled_df = show_df.copy()
        for extra in ["status_type","updated_at"]:
            if extra in df_sec.columns and extra not in styled_df.columns:
                styled_df[extra] = df_sec[extra].values

        # ── 桌機：一般表格 ／ 手機：卡片清單（用 expander 切換）──
        view_mode = st.radio("顯示模式", ["📋 表格", "📱 卡片（手機適用）"],
                             horizontal=True, key=f"view_{sec}", label_visibility="collapsed")

        if view_mode == "📋 表格":
            # ── HTML 表格：完全鎖死排序，顏色/紅字完整保留 ──
            import re as _re2
            COL_DISPLAY_NAMES = {
                "status":"施工順序","completion":"完成率","materials":"備料",
                "case_no":"案號","project_name":"工程名稱","client":"業主",
                "tracking":"備註","drawing":"製造圖面","pipe_support":"管撐製作",
                "welding":"點焊","nde":"焊道NDE","sandblast":"噴砂",
                "assembly":"組立*","painting":"噴漆","pressure_test":"試壓",
                "handover":"交站","handover_year":"年份","contact":"對應窗口",
            }
            disp_cols = [c for c in DISPLAY_COLS if c in df_sec.columns]

            # 表頭
            th_html = "".join(
                f'<th style="background:#1a3a5c;color:#fff;padding:6px 8px;'
                f'white-space:nowrap;font-size:12px;border:1px solid #2a5080;">'
                f'{COL_DISPLAY_NAMES.get(c,c)}</th>'
                for c in disp_cols
            )
            # 表身
            rows_html = ""
            for _, row in df_sec.iterrows():
                st_key = str(row.get("status_type",""))
                bg = STATUS_CONFIG.get(st_key,{}).get("bg","#ffffff")
                upd = str(row.get("updated_at",""))
                cells = ""
                for c in disp_cols:
                    val = str(row.get(c,""))
                    # 偵測本週日期 → 紅字
                    date_hits = _re2.findall(
                        r"(?<!\d)(\d{1,2}/\d{1,2})(?!\d)|(\d{4}-\d{2}-\d{2})", val)
                    cell_style = f"background:{bg};padding:5px 7px;font-size:12px;border:1px solid #ddd;white-space:nowrap;color:#111;"
                    cell_val = val
                    for grp in date_hits:
                        raw = grp[0] or grp[1]
                        if is_this_week_str(raw):
                            cell_val = val.replace(
                                raw,
                                f'<span style="color:#c62828;font-weight:900">{raw}</span>')
                            break
                    cells += f'<td style="{cell_style}">{cell_val}</td>'
                rows_html += f"<tr>{cells}</tr>"

            table_html = f"""
            <div style="overflow-x:auto;max-height:420px;overflow-y:auto;">
            <table style="border-collapse:collapse;width:100%;font-family:sans-serif;">
              <thead><tr>{th_html}</tr></thead>
              <tbody>{rows_html}</tbody>
            </table></div>"""
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            # ── 手機卡片視圖 ──
            import re as _re
            for _, row in df_sec.iterrows():
                st_key = str(row.get("status_type","not_started"))
                bg_color = STATUS_CONFIG.get(st_key,{}).get("bg","#fff")
                border_color = STATUS_CONFIG.get(st_key,{}).get("btn","#ccc")
                status_label = STATUS_CONFIG.get(st_key,{}).get("label","")
                status_icon  = STATUS_CONFIG.get(st_key,{}).get("icon","")

                # 工序進度格子
                proc_html = ""
                for col, name in zip(PROCESS_COLS, PROCESS_NAMES):
                    val = str(row.get(col,""))
                    done = val.strip() not in ("","None","nan","-")
                    is_week = False
                    hits = _re.findall(r"(?<![\d])(\d{1,2}/\d{1,2})(?![\d])", val)
                    hits += _re.findall(r"(\d{4}-\d{2}-\d{2})", val)
                    for raw in hits:
                        if is_this_week_str(raw): is_week = True; break
                    cell_style = "background:#4caf50;color:#fff;" if done else "background:#eee;color:#999;"
                    if is_week: cell_style = "background:#ffcdd2;color:#c62828;font-weight:900;"
                    short = val[:6] if val else "—"
                    proc_html += (f"<span title='{name}: {val}' style='display:inline-block;"
                                  f"border-radius:4px;padding:2px 5px;font-size:10px;margin:2px;"
                                  f"{cell_style}'>{name[:2]}</span>")

                # 備註
                tracking = str(row.get("tracking",""))
                tracking_html = ""
                if tracking:
                    hits2 = _re.findall(r"(?<![\d])(\d{1,2}/\d{1,2})(?![\d])", tracking)
                    if any(is_this_week_str(h) for h in hits2):
                        tracking_html = f"<div class='card-red' style='font-size:13px;margin-top:4px;'>📝 {tracking}</div>"
                    else:
                        tracking_html = f"<div class='card-sub'>📝 {tracking}</div>"

                card = f"""
                <div style="background:{bg_color};border-radius:10px;padding:12px 14px;
                  margin-bottom:8px;border-left:5px solid {border_color};
                  box-shadow:0 1px 4px rgba(0,0,0,0.1);">
                  <div style="font-size:15px;font-weight:800;color:#0d2137;">
                    {row.get('project_name','')}
                  </div>
                  <div style="font-size:12px;color:#555;margin:3px 0;">
                    {status_icon} {status_label} &nbsp;|&nbsp; {row.get('client','')} &nbsp;|&nbsp; {row.get('case_no','')}
                  </div>
                  <div style="font-size:12px;color:#555;">
                    完成率：<strong>{row.get('completion','')}</strong> &nbsp;
                    交站：<strong>{row.get('handover','')} {row.get('handover_year','')}</strong>
                  </div>
                  <div style="margin-top:6px;">{proc_html}</div>
                  {tracking_html}
                </div>"""
                st.markdown(card, unsafe_allow_html=True)

        # ── 編輯區 ────────────────────────────────────────────
        with st.expander(f"✏️ 編輯【{sec}】（改完自動儲存）"):

            edit_df = df_sec[[c for c in show_cols + ["status_type","id"] if c != "_order"]].copy()
            for _c in edit_df.columns:
                edit_df[_c] = edit_df[_c].replace({"None":"","nan":"","NaN":""})
            edit_df["status_zh"] = edit_df["status_type"].map(STATUS_KEY_TO_ZH).fillna("")
            edit_df.insert(0, "🗑 刪除", False)   # 勾選欄放最前面

            original_df = edit_df.copy()
            edit_key    = f"edit_{sec}"

            def auto_save_callback(sec=sec, original_df=original_df):
                state = st.session_state.get(f"edit_{sec}")
                if state is None: return
                # ✅ 若本次變動只有勾選「🗑 刪除」欄，跳過自動儲存
                # 讓刪除按鈕有機會顯示出來
                edited_rows = state.get("edited_rows", {})
                only_delete_checked = all(
                    set(changes.keys()) == {"🗑 刪除"}
                    for changes in edited_rows.values()
                ) if edited_rows else False
                if only_delete_checked:
                    return   # 不儲存，不重整，讓按鈕正常顯示
                saved = do_save(sec, original_df, state)
                if saved > 0:
                    st.cache_data.clear()
                    st.toast(f"✅ 自動儲存 {saved} 筆！", icon="💾")

            edited = st.data_editor(
                edit_df,
                key=edit_key,
                on_change=auto_save_callback,
                column_config={
                    **{k:v for k,v in COL_CONFIG.items()
                       if k in edit_df.columns or k == "status_zh"},
                    "🗑 刪除": st.column_config.CheckboxColumn(
                        "🗑 刪除", help="勾選後按下方確認刪除", width="small"),
                },
                use_container_width=True,
                num_rows="dynamic",
                hide_index=True,
                column_order=["🗑 刪除","status_zh","status","completion","materials",
                              "case_no","project_name","client","tracking","drawing",
                              "pipe_support","welding","nde","sandblast","assembly",
                              "painting","pressure_test","handover","handover_year","contact"],
            )

            # 勾選刪除按鈕
            del_rows = edited[edited["🗑 刪除"] == True]
            if not del_rows.empty:
                st.warning(f"⚠️ 已勾選 {len(del_rows)} 列，按下方按鈕確認刪除")
                if st.button(f"🗑 確認刪除 {len(del_rows)} 列",
                             key=f"del_btn_{sec}", type="primary"):
                    deleted = 0
                    for _, row in del_rows.iterrows():
                        rid = str(row.get("id",""))
                        if rid and rid not in ("","None"):
                            try:
                                supabase.table("projects").delete().eq("id", rid).execute()
                                deleted += 1
                            except Exception as e:
                                st.toast(f"刪除失敗：{e}", icon="❌")
                    st.success(f"✅ 已刪除 {deleted} 列")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.caption("💡 修改後點擊其他地方自動儲存 ／ 末列空白列可新增 ／ 勾選🗑可刪除整列")

    # ── 重新整理按鈕 ──────────────────────────────────────
    st.divider()
    c1,c2,_ = st.columns([1,1,4])
    with c1:
        if st.button("🔄 重新整理（更新顏色）", use_container_width=True, type="primary"):
            refresh()
    with c2:
        if st.button("📄 匯出 PDF", use_container_width=True):
            st.session_state["show_pdf"] = True

    if st.session_state.get("show_pdf"):
        try:
            from fpdf import FPDF
            import tempfile, os, urllib.request
            font_path = "/tmp/NotoSansSC.otf"
            FONT_URLS = [
                "https://cdn.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf",
                "https://github.com/googlefonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf",
            ]
            if not os.path.exists(font_path):
                with st.spinner("下載中文字型中..."):
                    for url in FONT_URLS:
                        try:
                            urllib.request.urlretrieve(url, font_path)
                            if os.path.getsize(font_path) > 100_000: break
                            os.remove(font_path)
                        except: pass

            pdf = FPDF(orientation="L", format="A3")
            pdf.set_auto_page_break(auto=True, margin=10)
            pdf.add_font("ZH", "", font_path)
            HEADERS=["施工順序","完成率","備料","案號","工程名稱","業主","備註","製造圖面","管撐","研磨點焊","NDE","噴砂","組立","噴漆","試壓","交站","年份","窗口"]
            KEYS=["status","completion","materials","case_no","project_name","client","tracking","drawing","pipe_support","welding","nde","sandblast","assembly","painting","pressure_test","handover","handover_year","contact"]
            WIDTHS=[20,11,7,22,55,13,30,13,11,18,11,11,11,11,11,15,9,13]
            PDF_BG={"in_progress":(255,255,153),"pending":(204,232,255),"not_started":(255,255,255),"suspended":(255,224,178),"completed":(240,240,240)}
            for sec in SECTIONS:
                ds = df_all[df_all["section"]==sec] if not df_all.empty else pd.DataFrame()
                if ds.empty: continue
                pdf.add_page()
                pdf.set_font("ZH", size=13); pdf.set_text_color(10,35,80)
                pdf.cell(0,9,f"【{sec}】  ({today})  共{len(ds)}筆", new_x="LMARGIN", new_y="NEXT"); pdf.ln(1)
                pdf.set_font("ZH", size=7); pdf.set_fill_color(29,71,157); pdf.set_text_color(255,255,255)
                for h,w in zip(HEADERS,WIDTHS): pdf.cell(w,7,h,border=1,fill=True,align="C")
                pdf.ln(); pdf.set_font("ZH",size=6); pdf.set_text_color(30,30,30)
                for _,row in ds.iterrows():
                    rgb = PDF_BG.get(row.get("status_type",""),(255,255,255))
                    pdf.set_fill_color(*rgb)
                    for k,w in zip(KEYS,WIDTHS):
                        val = str(row.get(k,"") or "")
                        if len(val)>16: val=val[:15]+"…"
                        pdf.cell(w,6,val,border=1,fill=True)
                    pdf.ln()
            with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as tmp:
                pdf.output(tmp.name)
                with open(tmp.name,"rb") as f: pdf_bytes=f.read()
                os.unlink(tmp.name)
            fname=f"工程案執行進度_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button("⬇ 下載 PDF", pdf_bytes, file_name=fname, mime="application/pdf")
            st.session_state["show_pdf"] = False
        except Exception as e:
            st.error(f"PDF 失敗：{e}")

# ═══════════════════════════════════════════════════════
# PAGE 2：工時分析
# ═══════════════════════════════════════════════════════
with page_tab2:
    if df_all.empty:
        st.warning("尚無資料")
    else:
        st.markdown("### 📊 各工程站點天數分析")
        st.caption("從**管撐製作**開始，計算每個站點完成所需天數（依欄位日期推算）")

        a1, a2, a3 = st.columns(3)
        with a1: sec_filter  = st.selectbox("分區", ["全部"]+SECTIONS, key="ana_sec")
        with a2: year_filter = st.selectbox("年份", ["全部","116","115","114"], key="ana_year")
        with a3: sta_filter  = st.selectbox("狀態", ["全部"]+[v["label"] for v in STATUS_CONFIG.values()], key="ana_sta")

        df_ana = df_all.copy()
        if sec_filter  != "全部": df_ana = df_ana[df_ana["section"]==sec_filter]
        if year_filter != "全部": df_ana = df_ana[df_ana["handover_year"]==year_filter]
        if sta_filter  != "全部":
            key = STATUS_ZH_TO_KEY.get(sta_filter,"")
            if key: df_ana = df_ana[df_ana["status_type"]==key]

        if df_ana.empty:
            st.info("此條件下沒有資料")
        else:
            # ── 工序定義（從管撐製作開始）──
            STAGES = [
                ("pipe_support", "管撐製作"),
                ("welding",      "點焊"),
                ("nde",          "焊道NDE"),
                ("sandblast",    "噴砂"),
                ("assembly",     "組立"),
                ("painting",     "噴漆"),
                ("pressure_test","試壓"),
                ("handover",     "交站"),
            ]

            def parse_date(val: str):
                """解析 M/D 或 YYYY-MM-DD，補上當年年份"""
                import re as _r
                val = str(val).strip()
                if not val or val in ("None","nan","-",""): return None
                # 取第一個日期片段（欄位可能有備注文字）
                m = _r.search(r"(\d{1,2})/(\d{1,2})", val)
                if m:
                    year = datetime.now().year
                    try: return datetime(year, int(m.group(1)), int(m.group(2)))
                    except: pass
                try: return pd.to_datetime(val, errors="coerce").to_pydatetime()
                except: return None

            # ── 計算每筆工程的各站點天數 ──
            records = []
            for _, row in df_ana.iterrows():
                # 嚴格依序解析：空白欄位保留為 None，不跳接
                dates = []
                for col, name in STAGES:
                    raw = str(row.get(col,"")).strip()
                    # 欄位空白 → 明確記為 None，不計算該段
                    if not raw or raw in ("None","nan","-",""):
                        dates.append((name, None))
                    else:
                        dates.append((name, parse_date(raw)))

                # 需要至少 2 個「相鄰且都有日期」的站點才能計算
                has_any_pair = any(
                    dates[i][1] is not None and dates[i+1][1] is not None
                    for i in range(len(dates)-1)
                )
                if not has_any_pair: continue

                proj = {
                    "案號":     row.get("case_no",""),
                    "工程名稱": row.get("project_name",""),
                    "業主":     row.get("client",""),
                    "分區":     row.get("section",""),
                    "狀態":     STATUS_KEY_TO_ZH.get(row.get("status_type",""),""),
                }
                # 只計算「相鄰且兩邊都有日期」的區段，空白欄留空不計算
                for i in range(len(dates)-1):
                    n1, d1 = dates[i]
                    n2, d2 = dates[i+1]
                    if d1 is None or d2 is None:
                        continue   # 任一端空白 → 跳過，不填數字
                    days = (d2 - d1).days
                    if days >= 0:
                        proj[f"{n1}→{n2}"] = days

                # 總天數：管撐製作到最後一個有日期的站點
                filled_dates = [d for _, d in dates if d is not None]
                if len(filled_dates) >= 2:
                    proj["總天數"] = (filled_dates[-1] - filled_dates[0]).days

                records.append(proj)

            if not records:
                st.info("目前資料不足以計算天數（需要至少填寫 2 個以上的工序日期）")
            else:
                df_days = pd.DataFrame(records).fillna("")

                # ── 1. 各工程天數明細表 ──
                st.markdown("#### 📋 各工程站點天數明細")
                st.dataframe(df_days, use_container_width=True, hide_index=True,
                             height=min(500, 40+len(df_days)*35))

                st.divider()

                # ── 2. 各站點平均天數（只取數字欄）──
                st.markdown("#### 📊 各站點平均天數（所有工程）")
                day_cols = [c for c in df_days.columns if "→" in c or c == "總天數"]
                numeric_days = df_days[day_cols].apply(pd.to_numeric, errors="coerce")
                avg_days = numeric_days.mean().dropna().round(1)

                if not avg_days.empty:
                    avg_df = avg_days.reset_index()
                    avg_df.columns = ["站點區間", "平均天數"]
                    st.bar_chart(avg_df.set_index("站點區間")["平均天數"],
                                 color="#1a3a5c", use_container_width=True)

                    # 數字卡片
                    cols_m = st.columns(min(len(avg_df), 4))
                    for i, (_, r) in enumerate(avg_df.iterrows()):
                        cols_m[i % len(cols_m)].metric(r["站點區間"], f"{r['平均天數']} 天")
                else:
                    st.info("無法計算平均天數")

                st.divider()

                # ── 3. 最快 / 最慢工程（依總天數）──
                numeric_total = pd.to_numeric(df_days["總天數"], errors="coerce")
                df_days["_total"] = numeric_total
                df_valid = df_days[df_days["_total"].notna()].sort_values("_total")

                if len(df_valid) >= 2:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### 🚀 完成最快（總天數最少）")
                        top3 = df_valid.head(3)[["案號","工程名稱","總天數","狀態"]]
                        st.dataframe(top3, use_container_width=True, hide_index=True)
                    with c2:
                        st.markdown("#### 🐢 耗時最長（總天數最多）")
                        bot3 = df_valid.tail(3)[["案號","工程名稱","總天數","狀態"]].sort_values("總天數", ascending=False)
                        st.dataframe(bot3, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════
# PAGE 3：生產工時儀表板
# ═══════════════════════════════════════════════════════
with page_tab3:
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        PLOTLY_OK = True
    except ImportError:
        PLOTLY_OK = False
        st.error("請在 requirements.txt 加入 plotly，重新部署後再使用。")

    if PLOTLY_OK:
        FONT = "Microsoft JhengHei, PingFang TC, Heiti TC, sans-serif"
        def apply_font(fig):
            fig.update_layout(font=dict(family=FONT,size=13),title_font=dict(family=FONT,size=15),
                              legend=dict(font=dict(family=FONT)),paper_bgcolor="white",plot_bgcolor="#f8faff")
            return fig

        @st.cache_data(ttl=30)
        def load_work_logs() -> pd.DataFrame:
            try:
                res = supabase.table("work_logs").select("*").order("start_time",desc=True).execute()
                if not res.data: return pd.DataFrame()
                df = pd.DataFrame(res.data)
                df["start_time"]     = pd.to_datetime(df["start_time"],  errors="coerce")
                df["end_time"]       = pd.to_datetime(df["end_time"],    errors="coerce")
                df["actual_hours"]   = pd.to_numeric(df["actual_hours"],   errors="coerce")
                df["standard_hours"] = pd.to_numeric(df["standard_hours"], errors="coerce")
                return df.dropna(subset=["start_time"])
            except: return pd.DataFrame()

        st.markdown("""
        <div style="background:linear-gradient(135deg,#0a2540,#1a6b3c);
          padding:12px 20px;border-radius:8px;margin-bottom:14px;">
          <div style="color:#fff;font-size:18px;font-weight:900;letter-spacing:2px;">⏱ 生產工時分析儀表板</div>
          <div style="color:#a8d5b5;font-size:12px;margin-top:3px;">資料來源：work_logs 資料表 ／ 即時同步</div>
        </div>
        """, unsafe_allow_html=True)

        df_wl = load_work_logs()
        if df_wl.empty:
            st.warning("⚠️ 尚無工時資料，或 `work_logs` 資料表尚未建立。")
            st.code("""
CREATE TABLE work_logs (
  id             bigint generated always as identity primary key,
  order_no       text, process_name text, operator text,
  start_time     timestamptz, end_time timestamptz,
  actual_hours   numeric, standard_hours numeric,
  notes text, created_at timestamptz default now()
);
INSERT INTO work_logs (order_no,process_name,operator,start_time,end_time,actual_hours,standard_hours) VALUES
('WO-001','焊接','張三','2026-02-20 08:00','2026-02-20 12:00',4.0,3.5),
('WO-002','噴漆','王五','2026-02-21 08:00','2026-02-21 11:30',3.5,2.5),
('WO-003','組立','趙六','2026-02-24 08:00','2026-02-24 14:00',6.0,4.5);
            """, language="sql")
        else:
            d1,d2,d3,d4 = st.columns(4)
            mn,mx = df_wl["start_time"].dt.date.min(), df_wl["start_time"].dt.date.max()
            with d1: date_from = st.date_input("開始日期",value=mn,min_value=mn,max_value=mx)
            with d2: date_to   = st.date_input("結束日期",value=mx,min_value=mn,max_value=mx)
            with d3: sel_op    = st.selectbox("人員",["全部人員"]+sorted(df_wl["operator"].dropna().unique().tolist()))
            with d4: sel_proc  = st.selectbox("工序",["全部工序"]+sorted(df_wl["process_name"].dropna().unique().tolist()))
            df_f = df_wl[(df_wl["start_time"].dt.date>=date_from)&(df_wl["start_time"].dt.date<=date_to)].copy()
            if sel_op   != "全部人員": df_f = df_f[df_f["operator"]==sel_op]
            if sel_proc != "全部工序": df_f = df_f[df_f["process_name"]==sel_proc]
            if df_f.empty: st.warning("此條件無資料")
            else:
                df_f["效率比%"] = df_f.apply(lambda r: round(r["actual_hours"]/r["standard_hours"]*100,1) if pd.notna(r["standard_hours"]) and r["standard_hours"]>0 else None,axis=1)
                df_f["超時"] = df_f["效率比%"].apply(lambda x: pd.notna(x) and x>120)
                st.divider()
                k1,k2,k3,k4,k5 = st.columns(5)
                k1.metric("📋 工單數",df_f["order_no"].nunique()); k2.metric("👷 人員數",df_f["operator"].nunique())
                k3.metric("⏱ 總實際工時",f"{df_f['actual_hours'].sum():.1f} h"); k4.metric("📐 總標準工時",f"{df_f['standard_hours'].sum():.1f} h")
                avg_eff = df_f["效率比%"].mean()
                k5.metric("📊 平均效率",f"{avg_eff:.1f}%" if pd.notna(avg_eff) else "N/A",delta=f"{avg_eff-100:.1f}%" if pd.notna(avg_eff) else None)
                st.divider()
                r1l,r1r = st.columns(2)
                with r1l:
                    op_h = df_f.groupby("operator")["actual_hours"].sum().reset_index().rename(columns={"operator":"人員","actual_hours":"累計工時(h)"}).sort_values("累計工時(h)",ascending=False)
                    fig1 = px.bar(op_h,x="人員",y="累計工時(h)",color="累計工時(h)",color_continuous_scale="Blues",text="累計工時(h)")
                    fig1.update_traces(texttemplate="%{text:.1f}h",textposition="outside"); fig1.update_layout(showlegend=False,height=350)
                    st.markdown("#### 👷 人員累計工時"); st.plotly_chart(apply_font(fig1),use_container_width=True)
                with r1r:
                    ph = df_f.groupby("process_name")["actual_hours"].sum().reset_index().rename(columns={"process_name":"工序","actual_hours":"工時(h)"})
                    fig2 = px.pie(ph,names="工序",values="工時(h)",hole=0.35,color_discrete_sequence=px.colors.qualitative.Set3)
                    fig2.update_traces(textinfo="label+percent",textfont_size=12); fig2.update_layout(height=350)
                    st.markdown("#### 🔧 工序工時佔比"); st.plotly_chart(apply_font(fig2),use_container_width=True)
                dd = df_f.groupby(df_f["start_time"].dt.date).agg(actual=("actual_hours","sum"),standard=("standard_hours","sum")).reset_index().rename(columns={"start_time":"日期"})
                dd["效率比%"] = (dd["actual"]/dd["standard"]*100).round(1)
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(x=dd["日期"],y=dd["actual"],name="實際工時",marker_color="#2196f3"))
                fig3.add_trace(go.Bar(x=dd["日期"],y=dd["standard"],name="標準工時",marker_color="#4caf50",opacity=0.6))
                fig3.add_trace(go.Scatter(x=dd["日期"],y=dd["效率比%"],name="效率比%",yaxis="y2",mode="lines+markers",line=dict(color="#ff7043",width=2),marker=dict(size=6)))
                fig3.update_layout(barmode="group",height=350,yaxis=dict(title="工時(小時)"),yaxis2=dict(title="效率比(%)",overlaying="y",side="right",showgrid=False),legend=dict(orientation="h",y=1.1))
                st.markdown("#### 📈 每日效率比趨勢"); st.plotly_chart(apply_font(fig3),use_container_width=True)
                st.divider(); st.markdown("#### ⚠️ 超時警報")
                df_al = df_f[df_f["超時"]].copy()
                if df_al.empty: st.success("✅ 無超時工單！")
                else:
                    st.error(f"🔴 共 {len(df_al)} 筆超時工單")
                    al = df_al[["order_no","process_name","operator","start_time","actual_hours","standard_hours","效率比%"]].rename(columns={"order_no":"工單","process_name":"工序","operator":"人員","start_time":"開始","actual_hours":"實際(h)","standard_hours":"標準(h)"}).sort_values("效率比%",ascending=False)
                    al["開始"] = al["開始"].dt.strftime("%m-%d %H:%M")
                    def hl(row):
                        if row["效率比%"]>150: return ["background-color:#ffcdd2"]*len(row)
                        return ["background-color:#fff9c4"]*len(row)
                    st.dataframe(al.style.apply(hl,axis=1).format({"效率比%":"{:.1f}%"}),use_container_width=True,hide_index=True)

        with st.expander("➕ 新增工時記錄"):
            with st.form("add_worklog"):
                wc1,wc2,wc3 = st.columns(3)
                with wc1: w_order=st.text_input("工單編號",placeholder="WO-001"); w_process=st.text_input("工序名稱",placeholder="焊接")
                with wc2: w_op=st.text_input("執行人員",placeholder="張三"); w_std=st.number_input("標準工時(h)",min_value=0.0,step=0.5,value=2.0)
                with wc3: w_start=st.datetime_input("開始時間",value=datetime.now()); w_end=st.datetime_input("結束時間",value=datetime.now())
                w_notes=st.text_input("備註（選填）")
                if st.form_submit_button("✅ 新增",type="primary"):
                    try:
                        actual=(w_end-w_start).total_seconds()/3600
                        if actual<=0: st.error("結束時間需晚於開始時間")
                        else:
                            supabase.table("work_logs").insert({"order_no":w_order,"process_name":w_process,"operator":w_op,"start_time":w_start.isoformat(),"end_time":w_end.isoformat(),"actual_hours":round(actual,2),"standard_hours":w_std,"notes":w_notes}).execute()
                            st.success(f"✅ 已新增！實際工時：{actual:.2f} h")
                            st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"新增失敗：{e}")
