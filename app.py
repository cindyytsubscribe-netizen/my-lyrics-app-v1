import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="法日歌詞導師", layout="wide")

# --- 核心：強效偵錯連線 ---
def try_init_ai():
    if "GEMINI_API_KEY" not in st.secrets or st.secrets["GEMINI_API_KEY"] == "":
        return None, "尚未在 Secrets 填入 GEMINI_API_KEY"
    
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 1. 嘗試列出所有妳能用的型號
        available_models = [m.name for m in genai.list_models()]
        if not available_models:
            return None, "妳的 API Key 權限下找不到任何可用型號，請檢查 Google AI Studio 專案設定。"
        
        # 2. 挑選最強的型號
        target = next((m for m in available_models if "gemini-1.5-flash" in m or "gemini-3-flash" in m), available_models[0])
        return genai.GenerativeModel(target), None
    except Exception as e:
        # 這裡會噴出 Google 的原始錯誤
        return None, f"Google 伺服器回傳錯誤：{str(e)}"

model, debug_error = try_init_ai()

# --- 檔案庫邏輯 (保持建檔功能) ---
if 'song_db' not in st.session_state:
    st.session_state.song_db = {}

# --- 側邊欄：建檔管理 ---
with st.sidebar:
    st.header("📂 歌曲檔案庫")
    if st.session_state.song_db:
        choice = st.selectbox("選取收藏", ["-- 請選擇 --"] + list(st.session_state.song_db.keys()))
        if choice != "-- 請選擇 --":
            st.session_state.curr_song = st.session_state.song_db[choice]
    
    st.divider()
    st.subheader("💾 備份檔案")
    db_json = json.dumps(st.session_state.song_db, ensure_ascii=False)
    st.download_button("📩 下載備份 (my_lyrics.json)", db_json, file_name="my_lyrics.json")
    
    uploaded = st.file_uploader("📤 匯入備份", type="json")
    if uploaded:
        st.session_state.song_db = json.load(uploaded)
        st.success("匯入成功！")

# --- 主介面 ---
st.title("🎵 歌詞導師 (Debug 版)")

if debug_error:
    st.error(f"🆘 連線診斷報告：{debug_error}")
    st.info("💡 小技巧：請嘗試重新申請一個 API Key 並確認 `requirements.txt` 已更新。")
else:
    st.success(f"✅ AI 連線成功！目前使用型號：{model.model_name}")

# 輸入區
with st.expander("📝 錄入新歌", expanded=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        song_title = st.text_input("歌名", value=st.session_state.get('curr_song', {}).get('title', ''))
    with col2:
        lang = st.radio("語言", ["法文", "日文"], horizontal=True)
    
    lyrics = st.text_area("歌詞", value=st.session_state.get('curr_song', {}).get('lyrics', ''), height=150)
    
    if st.button("🚀 解析並存入檔案庫", use_container_width=True):
        if not model:
            st.error("AI 尚未連線，無法解析。但妳仍可手動輸入內容存檔。")
        elif song_title and lyrics:
            with st.spinner("AI 老師分析中..."):
                try:
                    res = model.generate_content(f"妳是專業語言老師，請翻譯這段{lang}歌詞為繁體中文，並詳細解釋單字與文法：\n{lyrics}")
                    st.session_state.song_db[song_title] = {"title": song_title, "lyrics": lyrics, "analysis": res.text, "lang": lang}
                    st.rerun()
                except Exception as e:
                    st.error(f"解析失敗：{e}")

# 顯示結果
if 'curr_song' in st.session_state or (not debug_error and song_title in st.session_state.song_db):
    song_data = st.session_state.get('curr_song') or st.session_state.song_db[song_title]
    st.divider()
    st.subheader(f"📖 學習筆記：{song_data['title']}")
    st.markdown(song_data["analysis"])
