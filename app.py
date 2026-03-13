import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="歌詞學習助手", layout="centered")

# --- 1. 自動尋找可用型號 (解決 NotFound 問題) ---
@st.cache_resource
def get_best_model():
    if "GEMINI_API_KEY" not in st.secrets:
        return None, "請設定 API Key"
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 向 Google 索取這把 Key 權限下所有可用的型號
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 依照優先順序挑選
        for target in ["gemini-1.5-flash", "gemini-3-flash", "gemini-pro"]:
            for actual_name in models:
                if target in actual_name:
                    return genai.GenerativeModel(actual_name), None
        
        if models: return genai.GenerativeModel(models[0]), None
        return None, "找不到可用型號"
    except Exception as e:
        return None, str(e)

model, error_msg = get_best_model()

# --- 2. 解析邏輯 ---
def safe_generate(prompt):
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        if "429" in str(e): return "⚠️ AI 老師累了，請等 30 秒再點下一個單字。"
        return f"❌ 錯誤：{str(e)}"

# --- 3. 介面設計 ---
st.title("🎵 歌詞學習助手 (終極穩定版)")

if error_msg:
    st.error(f"AI 初始化失敗：{error_msg}")
    st.stop()

lang = st.radio("選擇語言：", ["法文", "日文"], horizontal=True)
user_input = st.text_area("在此輸入歌詞：", height=150, placeholder="例如：Les rois du monde vivent au sommet")

if st.button("✨ 一次解析整首歌", use_container_width=True):
    if user_input:
        lines = [line.strip() for line in user_input.split('\n') if line.strip()]
        
        # --- 省額度核心：一次翻譯整首歌 ---
        with st.spinner('正在整首翻譯中...'):
            full_prompt = f"妳是專業語言老師，請將以下{lang}歌詞翻譯成繁體中文，每一句一行，不要多寫別的：\n" + "\n".join(lines)
            full_translation = safe_generate(full_prompt)
            translated_lines = full_translation.strip().split('\n')

        # --- 顯示結果 ---
        for idx, line in enumerate(lines):
            st.markdown(f"#### 🎤 {line}")
            
            # 顯示對應翻譯
            if idx < len(translated_lines):
                st.success(f"💡 {translated_lines[idx]}")
            
            # 單字按鈕
            words = line.split() if lang == "法文" else list(line)
            cols = st.columns(min(len(words), 5))
            for i, word in enumerate(words[:20]):
                with cols[i % 5]:
                    # 使用彈窗，節省空間且穩定
                    with st.popover(word, use_container_width=True):
                        st.write(f"🔍 解析：**{word}**")
                        # 只有點開彈窗，才會執行 AI 查詢
                        with st.spinner('查詢中...'):
                            explain_prompt = f"在歌詞『{line}』中，單字『{word}』的意思、原型與文法為何？請用繁體中文簡短回答。"
                            st.write(safe_generate(explain_prompt))
            st.divider()
    else:
        st.warning("請先輸入歌詞喔！")
