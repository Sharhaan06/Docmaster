import streamlit as st
import fitz  # PyMuPDF
import requests
from dotenv import load_dotenv
import os

# =============================
# 🔑 ENV & API KEY
# =============================
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# =============================
# 🎨 THEME & STYLE
# =============================

def inject_css(dark: bool):
    """Inject dynamic CSS based on the current theme (dark / light)."""
    bg = "#000000" if dark else "#ffffff"
    text = "#ffffff" if dark else "#000000"
    glow = "rgba(255,255,255,0.25)" if dark else "rgba(0,0,0,0.1)"
    input_bg = "#1e1e1e" if dark else "#f5f5f5"

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            html, body, [class^="css"] {{
                font-family: 'Inter', sans-serif;
                background-color: {bg} !important;
                color: {text} !important;
                transition: background-color 0.4s ease, color 0.4s ease;
            }}

            .block-container {{
                padding: 2rem 3rem;
            }}

            textarea, .stTextInput>div>div>input {{
                border-radius: 10px !important;
                padding: 10px !important;
                box-shadow: 0 0 10px {glow};
                background-color: {input_bg} !important;
                color: {text} !important;
            }}

            .stTextInput>div>div {{
                background-color: {input_bg} !important;
            }}

            .stButton>button {{
                background-color: #4b8bf4 !important;
                color: #fff !important;
                border-radius: 8px;
                padding: 0.45rem 1rem;
                font-weight: 600;
                transition: 0.25s all ease;
                box-shadow: 0 0 12px {glow};
            }}

            .stButton>button:hover {{
                filter: brightness(1.1);
                box-shadow: 0 0 18px {glow};
            }}

            .glow-box {{
                box-shadow: 0 0 15px {glow};
                padding: 1rem;
                border-radius: 10px;
                background-color: {'rgba(255,255,255,0.05)' if dark else 'rgba(0,0,0,0.05)'};
                margin-bottom: 1rem;
                overflow-x: auto;
            }}

            header, footer, .css-hxt7ib, .css-1v3fvcr.e1fqkh3o3, .css-1avcm0n.e1fqkh3o3 {{display: none !important;}}
        </style>
    """, unsafe_allow_html=True)

# =============================
# ⚙️ STREAMLIT PAGE CONFIG
# =============================
st.set_page_config(page_title="DocMaster", layout="centered")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Theme toggle checkbox (top right)
with st.container():
    col_left, col_toggle = st.columns([0.85, 0.15])
    with col_toggle:
        toggled = st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
        st.session_state.dark_mode = toggled

inject_css(st.session_state.dark_mode)

# =============================
# 🏷️ APP TITLE
# =============================
st.title("📄 DocMaster")

# =============================
# 🔧 UTILITY FUNCTIONS
# =============================

def extract_text_from_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def ask_gpt(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "max_tokens": 800,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": "You are a helpful document analyzer."},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        resp = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return f"❌ API error {resp.status_code}: {resp.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Request failed: {e}"

# =============================
# 📄 FILE UPLOADERS
# =============================
uploaded_file_1 = st.file_uploader("Upload PDF 1", type="pdf")
uploaded_file_2 = st.file_uploader("Upload PDF 2 (optional)", type="pdf")

text_1, text_2 = "", ""

# =============================
# 📑 PROCESS PDF 1
# =============================
if uploaded_file_1:
    text_1 = extract_text_from_pdf(uploaded_file_1)
    with st.expander("📃 PDF 1 Preview", expanded=True):
        st.markdown(f"<div class='glow-box'>{text_1[:1500]}</div>", unsafe_allow_html=True)

    query_1 = st.text_input("✏️ What should I extract from PDF 1?", placeholder="e.g., names, dates, contact numbers")
    if st.button("Analyze PDF 1"):
        if not query_1:
            st.warning("Please enter something to extract.")
        else:
            with st.spinner("Analyzing PDF 1…"):
                result = ask_gpt(
                    f"You are an AI that extracts specific information from documents. "
                    f"Do not explain anything, just extract only what is asked. "
                    f"Respond with bullet points or clean labels. "
                    f"Now extract this: {query_1}\n\n{text_1}"
                )
            st.markdown("### 📌 Extracted Info")
            st.markdown(f"<div class='glow-box'>{result}</div>", unsafe_allow_html=True)

# =============================
# 🆚 COMPARISON (if PDF 2)
# =============================
if uploaded_file_1 and uploaded_file_2:
    text_2 = extract_text_from_pdf(uploaded_file_2)
    with st.expander("📃 PDF 2 Preview", expanded=True):
        st.markdown(f"<div class='glow-box'>{text_2[:1500]}</div>", unsafe_allow_html=True)

    if st.button("Compare Documents"):
        with st.spinner("Comparing PDFs…"):
            diff_prompt = (
                "Compare these two documents and highlight key differences:\n\n"
                f"--- PDF 1 ---\n{text_1}\n\n--- PDF 2 ---\n{text_2}"
            )
            diff = ask_gpt(diff_prompt)
        st.markdown("### 🆚 Comparison Result")
        st.markdown(f"<div class='glow-box'>{diff}</div>", unsafe_allow_html=True)
