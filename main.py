import streamlit as st
from backend import (
    extract_text_from_pdf,
    get_text_from_url,
    tailor_full_cv,
    parse_response,
    add_missing_keywords_to_skills,
    convert_text_to_pdf,
    generate_diff_html
)
import openai

st.set_page_config(page_title="🤖 AI CV Tailoring Tool", layout="wide")
st.title("🤖 AI CV Tailoring Tool")

# --- Sidebar ---
st.sidebar.header("⚙️ Settings")
temperature = st.sidebar.slider("OpenAI Temperature", 0.0, 1.0, 0.3, 0.05)
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if openai_api_key:
    openai.api_key = openai_api_key
else:
    st.warning("Please set your OpenAI API key in Streamlit secrets.")
    st.stop()

# --- CV Upload ---
if "parsed_cv" not in st.session_state:
    st.session_state["parsed_cv"] = None
    st.session_state["cv_file_name"] = ""

if st.session_state["parsed_cv"] is None:
    cv_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
    if cv_file:
        st.session_state["parsed_cv"] = extract_text_from_pdf(cv_file)
        st.session_state["cv_file_name"] = cv_file.name
        st.success(f"CV '{cv_file.name}' loaded.")
else:
    st.success(f"✅ CV '{st.session_state['cv_file_name']}' already loaded.")
    if st.button("🔁 Reset CV"):
        st.session_state["parsed_cv"] = None
        st.session_state["cv_file_name"] = ""
        st.experimental_rerun()

# --- Job Description Input ---
jd_text = ""
jd_url = st.text_input("Or enter Job Description URL")

if jd_url and st.button("📥 Fetch Job Description"):
    jd_text = get_text_from_url(jd_url)
    if jd_text.startswith("Error"):
        st.error(jd_text)
        jd_text = ""
    else:
        st.success("Job description loaded from URL")
else:
    jd_text = st.text_area("Paste the Job Description here", height=300, key="jd_text_area")

# --- Tailoring ---
if st.button("✂️ Tailor My Full CV"):
    if not st.session_state["parsed_cv"]:
        st.error("Please upload your CV.")
    elif not jd_text:
        st.error("Please provide a job description.")
    else:
        with st.spinner("Processing..."):
            result = tailor_full_cv(st.session_state["parsed_cv"], jd_text, temperature)
            score, missing_keywords, tailored_cv, cover_letter = parse_response(result)
            tailored_cv = add_missing_keywords_to_skills(tailored_cv, missing_keywords)

        st.subheader("📊 ATS Match & Suggestions")
        st.write(f"**Matching Score:** {score}")
        st.write(f"**Missing Keywords:** {', '.join(missing_keywords) if missing_keywords else 'None'}")

        st.subheader("📝 Tailored CV")
        st.text_area("Tailored CV", value=tailored_cv, height=700)
        pdf_cv_path = convert_text_to_pdf(tailored_cv)
        with open(pdf_cv_path, "rb") as f:
            st.download_button("📥 Download Tailored CV", f, file_name="tailored_cv.pdf")

        st.subheader("📄 Cover Letter")
        st.text_area("Cover Letter", value=cover_letter, height=400)
        pdf_cl_path = convert_text_to_pdf(cover_letter)
        with open(pdf_cl_path, "rb") as f:
            st.download_button("📥 Download Cover Letter", f, file_name="cover_letter.pdf")

        st.subheader("🆚 Differences (Original vs Tailored)")
        diff_html = generate_diff_html(st.session_state["parsed_cv"], tailored_cv)
        st.markdown(diff_html, unsafe_allow_html=True)
