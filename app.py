import streamlit as st
import google.generativeai as genai
import json

# --- 1. 基礎設定 ---
st.set_page_config(page_title="法日歌詞導師", layout="wide")

# --- 2. 解決連線失敗 (NotFound 修復) ---
@st.cache_resource
def get_ai_model():
    if "GEMINI_API_KEY" not in st.secrets:
        return None, "請在 Secrets 設定 GEMINI_API_KEY"
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 嘗試所有可能的名稱
        for m_name in ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']:
            try:
                m = genai.GenerativeModel(m_name)
                m.generate_content("test") # 預先測試連線
                return m, None
            except:
                continue
        return None, "找不到可用模型，請檢查 API Key 權限。"
    except Exception as e:
        return None, str(e)

model, ai_error = get_ai_model()

# --- 3. 歌曲檔案庫邏輯 ---
if 'song_db' not in st.session_state:
    st.session_state.song_db = {} # 格式: {歌名: {"lyrics": ..., "results": ...}}

# --- 4. 側邊欄：管理妳的建檔 ---
with st.sidebar:
    st.header("📂 歌詞檔案庫")
    
    # 功能 A：從檔案庫載入 (如果已經有存檔)
    if st.session_state.song_db:
        choice = st.selectbox("我的收藏", ["-- 請選擇 --"] + list(st.session_state.song_db.keys()))
        if choice != "-- 請選擇 --":
            st.session_state.loaded_song = st.session_state.song_db[choice]
            st.success(f"已載入：{choice}")
    
    st.divider()
    
    # 功能 B：永久保存到手機 (下載/上傳)
    st.subheader("💾 永久保存備份")
    db_json = json.dumps(st.session_state.song_db, ensure_ascii=False)
    st.download_button("📩 下載整份歌單備份", db_json, file_name="my_lyrics_backup.json")
    
    uploaded_file = st.file_uploader("📤 匯入備份檔案", type="json")
    if uploaded_file:
        st.session_state.song_db = json.load(uploaded_file)
        st.rerun()

# --- 5. 主介面 ---
st.title("🎵 歌詞導師 (建檔版)")

# 輸入區
with st.expander("📝 匯入新歌曲", expanded=True):
    t_col, l_col = st.columns([2, 1])
    with t_col:
        song_title = st.text_input("歌名：", placeholder="例如：A quelle étoile")
    with l_col:
        lang = st.radio("語言：", ["法文", "日文"], horizontal=True)
    
    lyrics_content = st.text_area("歌詞內容：", height=150)
    
    if st.button("✨ 開始解析並自動存檔", use_container_width=True):
        if song_title and lyrics_content:
            if ai_error:
                st.error(f"AI 連線失敗：{ai_error}")
            else:
                with st.spinner('AI 老師正在努力中...'):
                    # 一次性解析 (省額度)
                    full_prompt = f"妳是專業老師，請翻譯這段{lang}歌詞為繁中，並解析其中 5 個重點單字：\n{lyrics_content}"
                    res = model.generate_content(full_prompt)
                    # 存入資料庫
                    st.session_state.song_db[song_title] = {
                        "lyrics": lyrics_content,
                        "lang": lang,
                        "analysis": res.text
                    }
                    st.toast("✅ 解析完成並已存入檔案庫")
        else:
            st.warning("請輸入歌名與內容")

# --- 6. 顯示結果 (這部分不消耗 API，直接從存檔讀取) ---
if 'loaded_song' in st.session_state or song_title in st.session_state.song_db:
    current_song = st.session_state.get('loaded_song') or st.session_state.song_db[song_title]
    st.divider()
    st.subheader(f"📖 學習筆記：{song_title if 'song_title' in locals() else choice}")
    st.markdown(current_song["analysis"])
    
    with st.expander("查看原文歌詞"):
        st.write(current_song["lyrics"])
