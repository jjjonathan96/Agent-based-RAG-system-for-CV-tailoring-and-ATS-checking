import streamlit as st
import openai

# Set your API key (replace with env var or config in prod)
openai.api_key = "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"

st.set_page_config(page_title="CV Tailoring App", layout="wide")

st.title("🎯 CV Tailoring with RAG")

# Sidebar options
with st.sidebar:
    st.header("Upload Your Documents")
    general_cv = st.file_uploader("📄 Upload General CV (PDF)", type=["pdf"])
    full_cv = st.file_uploader("📚 Upload Full Experience CV (PDF)", type=["pdf"])
    job_description = st.text_area("📝 Paste Job Description Here", height=300)

    if st.button("🔍 Tailor My CV"):
        if not job_description:
            st.warning("Please provide a job description.")
        else:
            # OpenAI call to extract job skills and 2 key experiences
            prompt = f"""
You are a career assistant. Given the following job description, extract:

1. A bullet list of required or preferred skills.
2. Two concise and relevant work experience summaries that a candidate should highlight.

Be brief and professional.

Job Description:
\"\"\"
{job_description}
\"\"\"
"""

            with st.spinner("Analyzing job description..."):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                result = response.choices[0].message.content
                st.session_state["job_analysis"] = result
                st.session_state["process"] = True

# Main area
if st.session_state.get("process"):
    st.subheader("📌 Tailored CV Preview")

    st.markdown("### 🧠 Extracted from Job Description:")
    st.markdown(st.session_state.get("job_analysis", ""))

    st.markdown("### ✨ Tailored CV Content:")
    st.markdown("**Summary:** Tailored summary here...")
    st.markdown("**Experience:** Tailored experience here...")
    st.markdown("**Skills:** Tailored skills here...")

    st.download_button("📥 Download Tailored CV (PDF)", data="PDF_DATA", file_name="Tailored_CV.pdf")

    with st.expander("✏️ Edit Tailored CV Before Download"):
        edited_text = st.text_area("Make edits here...", value="Tailored CV content...")
        st.download_button("📥 Download Edited CV", data=edited_text, file_name="Edited_Tailored_CV.txt")
