import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="歌詞學習助手", layout="centered")

# --- 1. 自動尋找可用型號的機制 ---
@st.cache_resource # 這樣才不會每次點按鈕都重新找一次，增加效率
def get_best_model():
    if "GEMINI_API_KEY" not in st.secrets:
        return None, "找不到 API Key！"
    
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 向 Google 索取清單
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順序：3-flash > 1.5-flash > 1.0-pro
        for target in ["gemini-3-flash", "gemini-1.5-flash", "gemini-pro"]:
            for actual_name in models:
                if target in actual_name:
                    return genai.GenerativeModel(actual_name), None
        
        # 如果都沒找到，拿第一個能用的
        if models:
            return genai.GenerativeModel(models[0]), None
        return None, "您的 API Key 目前沒有可用的型號。"
    except Exception as e:
        return None, str(e)

# 啟動 AI
model, error_msg = get_best_model()

if error_msg:
    st.error(f"❌ AI 老師出了一點狀況：{error_msg}")
    st.stop()

# --- 2. 介面設計 ---
st.title("🎵 歌詞學習助手")
st.write(f"🤖 目前使用的 AI 型號：`{model.model_name}`") # 讓妳知道目前是用哪一個

lang = st.radio("選擇語言：", ["法文", "日文"], horizontal=True)
user_input = st.text_area("在此輸入歌詞：", height=150, placeholder="例如：Les rois du monde vivent au sommet")

if st.button("✨ 開始解析歌詞", use_container_width=True):
    if user_input:
        lines = user_input.split('\n')
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            
            st.markdown(f"#### 🎤 {line}")
            
            try:
                # 執行翻譯
                with st.spinner('翻譯中...'):
                    res_trans = model.generate_content(f"請將這句{lang}歌詞翻譯成繁體中文：『{line}』")
                    st.caption(f"💡 翻譯：{res_trans.text}")

                # 單字按鈕
                words = line.split() if lang == "法文" else list(line)
                cols = st.columns(min(len(words), 7)) 
                for i, word in enumerate(words[:21]):
                    with cols[i % 7]:
                        if st.button(word, key=f"btn_{idx}_{i}"):
                            with st.chat_message("assistant"):
                                st.write(f"🔍 正在解析：**{word}**")
                                res_explain = model.generate_content(f"在歌詞『{line}』中，單字『{word}』的意思、原型與文法為何？請用繁體中文解釋。")
                                st.info(res_explain.text)
            except Exception as e:
                st.error(f"解析這行時發生錯誤：{str(e)}")
            st.divider()
    else:
        st.warning("請先輸入一段歌詞喔！")
