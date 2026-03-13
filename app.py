import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="歌詞學習助手", layout="centered")

# --- 1. AI 模型自動偵測 (維持妳上次成功的邏輯) ---
@st.cache_resource
def get_best_model():
    if "GEMINI_API_KEY" not in st.secrets:
        return None, "請設定 API Key"
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ["gemini-3-flash", "gemini-1.5-flash", "gemini-pro"]:
            for actual_name in models:
                if target in actual_name:
                    return genai.GenerativeModel(actual_name), None
        return genai.GenerativeModel(models[0]), None if models else "無可用型號"
    except Exception as e:
        return None, str(e)

model, error_msg = get_best_model()

# --- 2. 介面設計 ---
st.title("🎵 歌詞學習助手")

lang = st.radio("選擇語言：", ["法文", "日文"], horizontal=True)
user_input = st.text_area("在此輸入歌詞：", height=150, placeholder="例如：Aimer, c'est ce qu'y a d'plus beau")

if st.button("✨ 開始解析歌詞", use_container_width=True):
    if user_input:
        lines = user_input.split('\n')
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            
            st.markdown(f"#### 🎤 {line}")
            
            # 翻譯部分 (自動顯示)
            try:
                with st.spinner('翻譯中...'):
                    res_trans = model.generate_content(f"請將這句{lang}歌詞翻譯成繁體中文：『{line}』")
                    st.success(f"💡 {res_trans.text}")

                # --- 改良版：單字點擊區 ---
                words = line.split() if lang == "法文" else list(line)
                
                # 用容器把單字排整齊
                word_container = st.container()
                cols = st.columns(min(len(words), 5)) # 手機上一排 5 個字比較剛好
                
                for i, word in enumerate(words[:20]): # 限制每句最多 20 個字
                    with cols[i % 5]:
                        # 使用 popover，點開直接看解釋，不跳頁
                        with st.popover(word, use_container_width=True):
                            st.write(f"🔍 **{word}**")
                            with st.spinner('老師查字典中...'):
                                explain_prompt = f"在歌詞『{line}』中，單字『{word}』的意思、原型與文法為何？請用繁體中文簡短回答。"
                                res_explain = model.generate_content(explain_prompt)
                                st.write(res_explain.text)
            except Exception as e:
                st.error(f"連線失敗：{e}")
            st.divider()
    else:
        st.warning("請先輸入一段歌詞喔！")
