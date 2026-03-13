import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="歌詞學習助手", layout="centered")

# --- 1. AI 模型自動偵測 (快取優化) ---
@st.cache_resource
def get_best_model():
    if "GEMINI_API_KEY" not in st.secrets: return None, "請設定 API Key"
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash'), None # 1.5-flash 的免費額度通常比 3-flash 寬鬆一點

model, _ = get_best_model()

# --- 2. 新增快取功能：避免重複點擊同個單字浪費額度 ---
@st.cache_data(show_spinner=False)
def get_ai_response(prompt):
    response = model.generate_content(prompt)
    return response.text

# --- 3. 介面 ---
st.title("🎵 歌詞學習助手 (省流量版)")

lang = st.radio("選擇語言：", ["法文", "日文"], horizontal=True)
user_input = st.text_area("在此輸入歌詞：", height=150)

if st.button("✨ 一次解析全曲", use_container_width=True):
    if user_input:
        lines = [line.strip() for line in user_input.split('\n') if line.strip()]
        
        # --- 核心優化：一次翻譯整首歌 ---
        with st.spinner('正在整首翻譯中... (這只會消耗 1 次額度)'):
            full_prompt = f"妳是一位語言老師，請將以下這幾句{lang}歌詞翻譯成繁體中文，每一句一行：\n" + "\n".join(lines)
            full_translation = get_ai_response(full_prompt)
            translated_lines = full_translation.strip().split('\n')

        # --- 顯示結果 ---
        for idx, line in enumerate(lines):
            st.markdown(f"#### 🎤 {line}")
            
            # 顯示對應的翻譯 (如果 AI 回傳行數對得上)
            if idx < len(translated_lines):
                st.success(f"💡 {translated_lines[idx]}")
            
            # 單字彈窗 (點擊才會消耗額度)
            words = line.split() if lang == "法文" else list(line)
            cols = st.columns(min(len(words), 5))
            for i, word in enumerate(words[:20]):
                with cols[i % 5]:
                    with st.popover(word, use_container_width=True):
                        st.write(f"🔍 解析：**{word}**")
                        # 只有點開彈窗，才會執行這裡
                        explanation = get_ai_response(f"在歌詞『{line}』中，單字『{word}』的意思、原型與文法為何？請用繁體中文簡短回答。")
                        st.info(explanation)
            st.divider()
    else:
        st.warning("請先輸入歌詞喔！")
