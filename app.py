import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="歌詞學習助手", layout="wide")

# --- 1. AI 設定 ---
@st.cache_resource
def get_model():
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    return None

model = get_model()

# --- 2. 存檔功能 (使用 Session State) ---
if 'archive' not in st.session_state:
    st.session_state.archive = {} # 用來存歌曲內容：{歌名: 歌詞}

# --- 3. 側邊欄：檔案庫 ---
with st.sidebar:
    st.header("📂 我的歌詞庫")
    if st.session_state.archive:
        saved_song = st.selectbox("選取已建檔歌曲：", ["-- 請選擇 --"] + list(st.session_state.archive.keys()))
        if saved_song != "-- 請選擇 --":
            st.info(f"已載入：{saved_song}")
    else:
        st.write("目前尚無存檔")
    
    st.divider()
    st.write("💡 提示：輸入新歌詞後點擊「存入檔案庫」，下次就能直接從選單叫出來。")

# --- 4. 主介面 ---
st.title("🎵 歌詞學習助手 (含建檔功能)")

col1, col2 = st.columns([1, 1])
with col1:
    lang = st.radio("語言：", ["法文", "日文"], horizontal=True)
with col2:
    new_song_title = st.text_input("歌曲名稱：", placeholder="例如：Les Rois du monde")

# 這裡會自動填入從側邊欄選取的歌詞
current_lyrics = st.session_state.archive.get(saved_song, "") if 'saved_song' in locals() and saved_song != "-- 請選擇 --" else ""
user_input = st.text_area("歌詞內容：", value=current_lyrics, height=150)

# 功能按鈕
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 存入檔案庫", use_container_width=True):
        if new_song_title and user_input:
            st.session_state.archive[new_song_title] = user_input
            st.success(f"歌曲『{new_song_title}』已建檔！")
        else:
            st.warning("請填寫歌名與歌詞再存檔喔！")
with c2:
    run_btn = st.button("✨ 開始解析歌詞", use_container_width=True)

# --- 5. 解析與顯示邏輯 ---
if run_btn and user_input:
    lines = [l.strip() for l in user_input.split('\n') if l.strip()]
    for idx, line in enumerate(lines):
        st.markdown(f"#### 🎤 {line}")
        with st.spinner('翻譯中...'):
            res = model.generate_content(f"請將這句{lang}歌詞翻譯成繁體中文：『{line}』")
            st.success(f"💡 {res.text}")
        
        words = line.split() if lang == "法文" else list(line)
        cols = st.columns(min(len(words), 5))
        for i, word in enumerate(words[:20]):
            with cols[i % 5]:
                with st.popover(word, use_container_width=True):
                    st.write(f"🔍 **{word}**")
                    with st.spinner('查詢中...'):
                        exp = model.generate_content(f"在歌詞『{line}』中，單字『{word}』的意思、原型與文法為何？請用繁體中文簡短回答。")
                        st.write(exp.text)
        st.divider()
