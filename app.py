import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="歌詞導師", layout="centered")

# --- 1. AI 老師連線設定 ---
@st.cache_resource
def init_ai():
    if "GEMINI_API_KEY" not in st.secrets: return None, "請設定 API Key"
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 強制指定一個最穩定的型號
        return genai.GenerativeModel('models/gemini-1.5-flash'), None
    except Exception as e: return None, str(e)

model, ai_err = init_ai()

# --- 2. 檔案庫初始化 ---
if 'db' not in st.session_state: st.session_state.db = {}

# --- 3. 側邊欄：管理妳的歌單 ---
with st.sidebar:
    st.header("📂 我的歌詞檔案庫")
    if st.session_state.db:
        choice = st.selectbox("選取歌曲", ["-- 請選擇 --"] + list(st.session_state.db.keys()))
        if choice != "-- 請選擇 --":
            st.session_state.c_title = choice
            st.session_state.c_data = st.session_state.db[choice]
    st.divider()
    st.download_button("📩 下載備份到手機", json.dumps(st.session_state.db, ensure_ascii=False), "my_lyrics.json")
    up = st.file_uploader("📤 匯入備份檔", type="json")
    if up: st.session_state.db = json.load(up); st.rerun()

# --- 4. 主介面 ---
st.title("🎵 歌詞逐字解析")

t_col, l_col = st.columns([2, 1])
with t_col: 
    title = st.text_input("歌名", value=st.session_state.get("c_title", ""))
with l_col: 
    lang = st.radio("語言", ["法文", "日文"], horizontal=True)

lyrics = st.text_area("歌詞內容", value=st.session_state.get("c_data", {}).get("raw", ""), height=150)

if st.button("💾 存入檔案庫並解析", use_container_width=True):
    if title and lyrics:
        with st.spinner("AI 老師翻譯中..."):
            try:
                # 這裡把翻譯直接存起來，下次就不用重問
                res = model.generate_content(f"妳是專業翻譯。請將這段{lang}歌詞『逐句』翻譯成繁體中文。格式：原文=翻譯。歌詞內容：\n{lyrics}")
                trans_map = {}
                for item in res.text.split('\n'):
                    if '=' in item:
                        k, v = item.split('=', 1)
                        trans_map[k.strip()] = v.strip()
                
                st.session_state.db[title] = {"raw": lyrics, "lang": lang, "trans": trans_map}
                st.success("✅ 解析完成並已存檔！")
            except Exception as e:
                st.error(f"連線失敗：{e}")
    else: st.warning("請輸入歌名與內容")

# --- 5. 顯示結果 (這部分優先讀取存檔，不浪費連線) ---
if title in st.session_state.db:
    data = st.session_state.db[title]
    lines = [l.strip() for l in data["raw"].split('\n') if l.strip()]
    
    for idx, line in enumerate(lines):
        st.markdown(f"### {line}")
        # 從存檔拿翻譯
        line_trans = data["trans"].get(line, "（點擊按鈕重新解析翻譯）")
        st.info(f"👉 **{line_trans}**")
        
        # 逐字彈窗
        words = line.split() if data["lang"] == "法文" else list(line)
        cols = st.columns(min(len(words), 5))
        for i, word in enumerate(words[:15]):
            with cols[i % 5]:
                with st.popover(word, use_container_width=True):
                    if st.button("查單字", key=f"lex_{idx}_{i}"):
                        try:
                            # 這裡維持簡潔：原型、意思、文法
                            exp_p = f"單字『{word}』在歌詞『{line}』中的意思？請給：1.原型 2.意思 3.簡單文法。繁中簡答，不要廢話。"
                            st.write(model.generate_content(exp_p).text)
                        except: st.write("請稍候再試")
        st.divider()
