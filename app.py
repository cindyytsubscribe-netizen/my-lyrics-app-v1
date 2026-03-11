import streamlit as st
import google.generativeai as genai

# 設定網頁顯示方式
st.set_page_config(page_title="歌詞學習助手", layout="centered")

# 讀取後台設定的 API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 修改後的
    model = genai.GenerativeModel('models/gemini-1.5-flash')
else:
    st.error("請在 Secrets 設定中輸入您的 API Key！")

st.title("🎵 歌詞學習助手")
lang = st.radio("選擇語言：", ["法文", "日文"], horizontal=True)
user_input = st.text_area("在此輸入歌詞：", height=150)

if st.button("✨ 開始解析歌詞", use_container_width=True):
    if user_input:
        lines = user_input.split('\n')
        for idx, line in enumerate(lines):
            if not line.strip(): continue
            st.markdown(f"#### 🎤 {line}")
            
            # AI 翻譯
            with st.spinner('翻譯中...'):
                res_trans = model.generate_content(f"請將這句{lang}歌詞翻譯成繁體中文：『{line}』")
                st.caption(f"💡 翻譯：{res_trans.text}")

            # 拆解單字按鈕 (法文空格分詞，日文逐字拆分)
            words = line.split() if lang == "法文" else list(line)
            cols = st.columns(min(len(words), 8))
            for i, word in enumerate(words[:24]):
                with cols[i % len(cols)]:
                    if st.button(word, key=f"btn_{idx}_{i}"):
                        with st.spinner('分析中...'):
                            res_explain = model.generate_content(f"在歌詞『{line}』中，單字『{word}』的意思、原型與文法為何？請用繁體中文解釋。")
                            st.info(res_explain.text)
            st.divider()
