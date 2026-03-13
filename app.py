import streamlit as st
import google.generativeai as genai
import json

# --- 1. AI 初始化 (穩定連線邏輯) ---
st.set_page_config(page_title="歌詞導師", layout="centered")

@st.cache_resource
def get_ai():
    if "GEMINI_API_KEY" not in st.secrets: return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 嘗試穩定型號
    for m_name in ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']:
        try:
            m = genai.GenerativeModel(m_name)
            m.generate_content("test")
            return m
        except: continue
    return None

model = get_ai()

# --- 2. 檔案庫邏輯 (Session State) ---
if 'db' not in st.session_state: st.session_state.db = {}

# --- 3. 側邊欄：檔案管理 ---
with st.sidebar:
    st.header("📂 歌曲檔案庫")
    if st.session_state.db:
        choice = st.selectbox("我的收藏", ["-- 選擇歌曲 --"] + list(st.session_state.db.keys()))
        if choice != "-- 選擇歌曲 --":
            st.session_state.lyrics = st.session_state.db[choice]["l"]
            st.session_state.lang = st.session_state.db[choice]["g"]
            st.session_state.title = choice
    st.divider()
    st.download_button("📩 備份歌單到手機", json.dumps(st.session_state.db, ensure_ascii=False), "lyrics.json")
    up = st.file_uploader("📤 匯入備份", type="json")
    if up: st.session_state.db = json.load(up); st.rerun()

# --- 4. 主介面：極簡輸入 ---
st.title("🎵 歌詞逐字解析")

t_col, l_col = st.columns([2, 1])
with t_col: 
    title = st.text_input("歌名", value=st.session_state.get("title", ""))
with l_col: 
    lang = st.radio("語言", ["法文", "日文"], index=0 if st.session_state.get("lang") == "法文" else 1, horizontal=True)

lyrics = st.text_area("歌詞內容", value=st.session_state.get("lyrics", ""), height=150)

c1, c2 = st.columns(2)
with c1:
    if st.button("💾 存入檔案庫", use_container_width=True):
        if title and lyrics:
            st.session_state.db[title] = {"l": lyrics, "g": lang}
            st.toast("✅ 已存檔")
with c2:
    start = st.button("🚀 開始翻譯", use_container_width=True)

# --- 5. 顯示結果：逐句與逐字 ---
if start and lyrics:
    lines = [l.strip() for l in lyrics.split('\n') if l.strip()]
    for idx, line in enumerate(lines):
        # 顯示原文
        st.markdown(f"### {line}")
        
        # 逐句翻譯 (直接顯示，不廢話)
        try:
            trans_p = f"妳是專業翻譯。請直接給出這句{lang}歌詞的中文翻譯，不要任何解釋：『{line}』"
            st.write(f"👉 **{model.generate_content(trans_p).text}**")
        except: st.write("⚠️ 翻譯連線中...")

        # 逐字翻譯 (點擊單字顯示彈窗)
        words = line.split() if lang == "法文" else list(line)
        cols = st.columns(min(len(words), 5))
        for i, word in enumerate(words[:15]):
            with cols[i % 5]:
                with st.popover(word, use_container_width=True):
                    try:
                        explain_p = f"單字：『{word}』。請提供：1.原型 2.意思 3.簡單文法。用條列式，不要廢話。"
                        st.markdown(model.generate_content(explain_p).text)
                    except: st.write("請稍候再點")
        st.divider()
