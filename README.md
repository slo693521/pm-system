# ⚙ 工程案執行進度管理系統

Streamlit + Supabase 版本

---

## 部署步驟

### 第一步：建立 Supabase 資料表

1. 去 [supabase.com](https://supabase.com) 免費註冊，建立新專案
2. 進入 **SQL Editor**，貼上並執行以下 SQL：

```sql
create table projects (
  id bigint generated always as identity primary key,
  section text,
  status text,
  completion text,
  materials text,
  case_no text,
  project_name text,
  client text,
  tracking text,
  plan_doc text,
  drawing text,
  pipe_support text,
  welding text,
  nde text,
  sandblast text,
  assembly text,
  painting text,
  pressure_test text,
  handover text,
  handover_year text,
  est_delivery text,
  notes text,
  contact text,
  closed text,
  status_type text,
  created_at timestamptz default now()
);
```

3. 去 **Settings → API**，記下：
   - `Project URL`
   - `anon public key`

---

### 第二步：匯入初始資料

```bash
pip install supabase
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="eyJ..."
python seed_data.py
```

> 只需執行一次！之後資料都存在 Supabase。

---

### 第三步：上傳到 GitHub

1. 在 GitHub 建立新 repo（例如 `pm-system`）
2. 上傳所有檔案（**不要**上傳 `.streamlit/secrets.toml`）

```bash
git init
git add .
git commit -m "初始化工程進度系統"
git remote add origin https://github.com/你的帳號/pm-system.git
git push -u origin main
```

---

### 第四步：部署到 Streamlit Cloud

1. 去 [share.streamlit.io](https://share.streamlit.io) 登入（用 GitHub 帳號）
2. 點 **New app**
3. 選你的 repo → branch: `main` → Main file: `app.py`
4. 點 **Advanced settings → Secrets**，填入：

```toml
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJ..."
```

5. 點 **Deploy！**

完成後會得到網址：`https://你的帳號-pm-system.streamlit.app`

---

## 本機執行

```bash
pip install -r requirements.txt

# 建立 .streamlit/secrets.toml
mkdir .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 填入你的 Supabase 金鑰

streamlit run app.py
```

---

## 功能

- ✅ 多分區顯示（主要工程 / 偉鴻 / 材料案）
- ✅ 狀態篩選（製作中 / 待交站 / 未開始 / 已完成 / 停工）
- ✅ 年份篩選（114 / 115）
- ✅ 關鍵字搜尋
- ✅ 直接雙擊編輯儲存格
- ✅ 儲存後同步到 Supabase（多人共用）
- ✅ 匯出 PDF

## 顏色說明

| 顏色 | 狀態 |
|------|------|
| 🟡 黃色 | 製作中 |
| 🔵 淺藍 | 待交站 |
| ⬜ 白色 | 未開始 |
| 🟠 橘色 | 停工 |
| ⬜ 淺灰 | 已完成 |
