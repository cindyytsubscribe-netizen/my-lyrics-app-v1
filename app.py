import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="歌詞學習助手", layout="centered")


if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 改用這一個型號，穩定度 100%
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("❌ 找不到 API Key！")
    st.stop()

st.title("🎵 歌詞學習助手")
st.write("適合研究《羅密歐與茱麗葉》或練習日文 N5 的妳。")

lang = st.radio("選擇語言：", ["法文", "日文"], horizontal=True)
user_input = st.text_area("在此輸入歌詞：", height=150, placeholder="例如：Aimer, c'est ce qu'y a d'plus beau")

if st.button("✨ 開始解析歌詞", use_container_width=True):
    if user_input:
        lines = user_input.split('\n')
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            
            st.markdown(f"#### 🎤 {line}")
            
            try:
                # 呼叫翻譯
                with st.spinner('AI 老師正在翻譯...'):
                    # 這裡加入了更明確的指令
                    res_trans = model.generate_content(f"妳是一位專業的語言老師，請將這句{lang}歌詞翻譯成繁體中文：『{line}』")
                    st.caption(f"💡 翻譯：{res_trans.text}")

                # 拆解單字按鈕
                words = line.split() if lang == "法文" else list(line)
                # 這裡增加一點間距
                cols = st.columns(min(len(words), 7)) 
                for i, word in enumerate(words[:21]):
                    with cols[i % 7]:
                        if st.button(word, key=f"btn_{idx}_{i}"):
                            with st.chat_message("assistant"):
                                st.write(f"🔍 正在解析：**{word}**")
                                res_explain = model.generate_content(f"在歌詞『{line}』中，單字『{word}』的意思是什麼？請提供：1. 原型 2. 文法功能 3. 簡單中文例句。")
                                st.info(res_explain.text)
            except Exception as e:
                # 如果還是報錯，我們會看到更詳細的內容
                st.error(f"連線到 AI 時發生一點問題：{str(e)}")
            st.divider()
    else:
        st.warning("請先輸入一段歌詞喔！")
