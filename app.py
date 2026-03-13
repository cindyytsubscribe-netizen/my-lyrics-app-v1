import streamlit as st
import google.generativeai as genai

# --- 1. 基礎設定 ---
st.set_page_config(page_title="法日歌詞導師", layout="wide")

# --- 2. 終極 AI 連線邏輯 (解決 NotFound 問題) ---
@st.cache_resource
def init_ai():
    if "GEMINI_API_KEY" not in st.secrets:
        return None, "找不到 API Key"
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 自動尋找可用型號
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 優先順序
        for target in ["gemini-1.5-flash", "gemini-3-flash", "gemini-pro"]:
            for m_name in available_models:
                if target in m_name:
                    return genai.GenerativeModel(m_name), None
        return genai.GenerativeModel(available_models[0]), None
    except Exception as e:
        return None, str(e)

model, error_msg = init_ai()

# --- 3. 檔案庫存檔邏輯 (Session State) ---
if 'my_archive' not in st.session_state:
    st.session_state.my_archive = {}

# --- 4. 側邊欄：管理妳的歌單 ---
with st.sidebar:
    st.header("📂 我的歌詞檔案庫")
    
    if st.session_state.my_archive:
        selected_song = st.selectbox("選取已存歌曲：", ["-- 請選擇 --"] + list(st.session_state.my_archive.keys()))
        if selected_song != "-- 請選擇 --":
            # 載入存檔內容
            st.session_state.current_lyrics = st.session_state.my_archive[selected_song]["content"]
            st.session_state.current_lang = st.session_state.my_archive[selected_song]["lang"]
            st.success(f"已載入：{selected_song}")
    else:
        st.write("目前尚無存檔。")
    
    st.divider()
    st.caption("註：目前的存檔在瀏覽器重新整理後會消失。若要永久保存，建議將歌詞存入妳的 Google Keep 清單中。")

# --- 5. 主介面設計 ---
st.title("🎵 歌詞學習助手")

if error_msg:
    st.error(f"AI 連線失敗：{error_msg}")
    st.stop()

# 輸入區
col_l, col_r = st.columns([1, 1])
with col_l:
    lang = st.radio("語言：", ["法文", "日文"], 
                    index=0 if st.session_state.get("current_lang") == "法文" else 1, 
                    horizontal=True)
with col_r:
    song_name = st.text_input("歌曲名稱：", placeholder="例如：A quelle étoile")

lyric_input = st.text_area("歌詞內容：", 
                          value=st.session_state.get("current_lyrics", ""), 
                          height=150)

# 功能按鈕
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 存入檔案庫", use_container_width=True):
        if song_name and lyric_input:
            st.session_state.my_archive[song_name] = {"content": lyric_input, "lang": lang}
            st.toast(f"✅ {song_name} 已成功存檔！")
        else:
            st.warning("請輸入歌名與歌詞再存檔。")

with c2:
    start_analyze = st.button("✨ 開始解析歌詞", use_container_width=True)

# --- 6. 解析與顯示 ---
if start_analyze and lyric_input:
    lines = [l.strip() for l in lyric_input.split('\n') if l.strip()]
    
    # 這裡加入一個簡單的防崩潰處理
    try:
        for idx, line in enumerate(lines):
            st.markdown(f"#### 🎤 {line}")
            
            # 翻譯 (加上 try-except 避免單行錯誤毀掉全部)
            try:
                with st.spinner('翻譯中...'):
                    res = model.generate_content(f"請將這句{lang}歌詞翻譯成繁體中文：『{line}』")
                    st.success(f"💡 {res.text}")
            except:
                st.error("翻譯暫時失效，請稍後再試。")

            # 單字彈窗
            words = line.split() if lang == "法文" else list(line)
            cols = st.columns(min(len(words), 5))
            for i, word in enumerate(words[:20]):
                with cols[i % 5]:
                    with st.popover(word, use_container_width=True):
                        st.write(f"🔍 **{word}**")
                        with st.spinner('查詢中...'):
                            try:
                                exp = model.generate_content(f"在歌詞『{line}』中，單字『{word}』的意思、原型與文法為何？請用繁體中文簡短回答。")
                                st.info(exp.text)
                            except:
                                st.write("查詢太頻繁，請等 30 秒。")
            st.divider()
    except Exception as e:
        st.error(f"解析發生錯誤：{e}")
