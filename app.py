import streamlit as st
import openai
import pdfplumber
from fpdf import FPDF
import tempfile
import re

score, missing_keywords, tailored_cv, cover_letter = 0, '', '', ''

# --- UI Setup ---
st.set_page_config(page_title="AI CV Tailoring", layout="wide")
st.title("🤖 AI CV + Cover Letter Tailoring Tool")

# --- API Key Input ---
#openai.api_key = st.text_input("Enter your OpenAI API Key", type="password")
openai.api_key = st.secrets["OPENAI_API_KEY"]
# --- Extract PDF Text ---
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

# --- Tailor CV via GPT ---
@st.cache_data(show_spinner=False)
def tailor_full_cv(cv_text, jd_text):
    prompt = f"""
You are an expert career assistant. Perform the following:
1. Compare the CV and Job Description and calculate a matching score (0-100).
2. List important keywords from the Job Description that are missing in the CV.
3. Rewrite the full CV to tailor it to the Job Description and only change in work expereince check how many work experience in cv then modified the existing work experience with job description maximum three lines and in skills don't remove old keywords append the missing one.
4. Write a concise, ATS-optimized cover letter for the job.

Return the response in this format:
---
Matching Score: <number>

Missing Keywords:
- keyword1
- keyword2

Tailored CV:
<full tailored CV>

Cover Letter:
<cover letter>
---
    
CV:
{cv_text}

Job Description:
{jd_text}
"""
    response = openai.ChatCompletion.create(
        model="o4-mini",
        messages=[
            {"role": "system", "content": "You are a professional CV and cover letter assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=1
    )
    return response.choices[0].message.content

# --- Parse GPT Response ---
def parse_response(response_text):
    match_score = re.search(r"Matching Score:\s*(\d+)", response_text)
    score = int(match_score.group(1)) if match_score else None

    missing_kw_block = re.search(r"Missing Keywords:\s*((?:- .*\n)+)", response_text)
    missing_keywords = []
    if missing_kw_block:
        missing_keywords = [line.strip("- ").strip() for line in missing_kw_block.group(1).splitlines()]

    tailored_cv_block = re.search(r"Tailored CV:\s*(.*?)\nCover Letter:", response_text, re.DOTALL)
    tailored_cv = tailored_cv_block.group(1).strip() if tailored_cv_block else ""

    cover_letter_block = re.search(r"Cover Letter:\s*(.*)", response_text, re.DOTALL)
    cover_letter_temp = cover_letter_block.group(1).strip() if cover_letter_block else ""
    cover_letter = " ".join(cover_letter_temp.split('?'))
    return score, missing_keywords, tailored_cv, cover_letter

# --- Improve Skills Section ---
def add_missing_keywords_to_skills(cv_text, missing_keywords):
    skills_section_pattern = re.compile(r"(Skills[:\n]+)(.*?)(\n\n|$)", re.DOTALL | re.IGNORECASE)

    def replacer(match):
        skills_header = match.group(1)
        skills_content = match.group(2).strip()
        current_skills = set(re.split(r",|\n", skills_content))
        updated_skills = current_skills.union(set(missing_keywords))
        return f"{skills_header}{', '.join(sorted(updated_skills))}\n\n"

    if skills_section_pattern.search(cv_text):
        return skills_section_pattern.sub(replacer, cv_text)
    else:
        return cv_text.strip() + "\n\nSkills:\n" + ", ".join(sorted(set(missing_keywords))) + "\n"
# clean unicode
def clean_text_for_pdf(text):
    replacements = {
        "—": "-",
        "–": "-",
        "“": "\"",
        "”": "\"",
        "’": "'",
        "•": "-",
        "…": "...",
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2003": " ",  # em space ← ADD THIS LINE
        "\u2002": " ",  # en space (optional)
        "\u2009":" ",
        "\u200a":" ",
        "\u2502":" ",
        "\u2010":" ",
        "\u00a0": " ",  # non-breaking space (optional)
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text


# --- Create PDF from Text ---
def convert_text_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=11)
    line_height = pdf.font_size * 2
    text = clean_text_for_pdf(text)
    for line in text.split('\n'):
        safe_line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, line_height, safe_line)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name

def convert_text_to_pdf_one_page(text):
    pdf = FPDF(format='A4')
    pdf.add_page()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=False)  # no page breaks

    pdf.set_font("Arial", size=10)
    line_height = pdf.font_size * 1.5
    max_height = 277  # approx usable height on A4 in mm (297 - margins)

    y_start = pdf.get_y()
    height_used = 0

    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            # small vertical gap for empty lines
            height_used += line_height * 0.5
            if height_used > max_height:
                break
            pdf.ln(line_height * 0.5)
            continue

        # Detect section headings (simple heuristic: all uppercase or ends with ':')
        if line.isupper() or line.endswith(":"):
            pdf.set_font("Arial", "B", 10)
        else:
            pdf.set_font("Arial", size=10)

        # Estimate if this line fits
        if height_used + line_height > max_height:
            break

        # Write the line with wrapping
        pdf.multi_cell(0, line_height, line)
        height_used += line_height

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name


# --- Session Setup ---
if "parsed_cv" not in st.session_state:
    st.session_state["parsed_cv"] = None
if "tailored_cv" not in st.session_state:
    st.session_state["tailored_cv"] = ""
if "cover_letter" not in st.session_state:
    st.session_state["cover_letter"] = ""

# --- Upload CV ---
if st.session_state["parsed_cv"] is None:
    cv_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
    if cv_file:
        with st.spinner("Extracting CV..."):
            st.session_state["parsed_cv"] = extract_text_from_pdf(cv_file)
            st.success("✅ CV extracted.")
else:
    st.success("✅ CV already loaded.")
    if st.button("🔁 Reset CV"):
        for key in ["parsed_cv", "tailored_cv", "cover_letter"]:
            st.session_state[key] = None if key == "parsed_cv" else ""
        st.experimental_rerun()

# --- Job Description Input ---
jd_input = st.text_area("Paste the Job Description here",height=500)

# --- Tailor Button ---
if st.button("✨ Tailor My CV & Cover Letter") and st.session_state["parsed_cv"] and jd_input:
    with st.spinner("Processing with GPT..."):
        result = tailor_full_cv(st.session_state["parsed_cv"], jd_input)
        score, missing_keywords, tailored_cv, cover_letter = parse_response(result)
        tailored_cv = add_missing_keywords_to_skills(tailored_cv, missing_keywords)

        st.session_state["tailored_cv"] = tailored_cv
        st.session_state["cover_letter"] = cover_letter

# --- Show Results ---
if st.session_state["tailored_cv"]:
    st.subheader("📊 Matching Score & Keyword Gap")
    st.write(f"**Score:** {score}/100")
    st.write(f"**Missing Keywords:** {', '.join(missing_keywords) if missing_keywords else 'None'}")

    st.subheader("📄 Tailored CV")
    st.text_area("Tailored CV Preview", value=st.session_state["tailored_cv"], height=500)
    #pdf_cv = convert_text_to_pdf(st.session_state["tailored_cv"])
    pdf_cv = convert_text_to_pdf_one_page(clean_text_for_pdf(st.session_state["tailored_cv"]))
    with open(pdf_cv, "rb") as f:
        st.download_button("⬇️ Download Tailored CV (PDF)", f.read(), file_name="tailored_cv.pdf", mime="application/pdf")

    st.subheader("✉️ Cover Letter")
    st.text_area("Cover Letter Preview", value=st.session_state["cover_letter"], height=400)
    pdf_cl = convert_text_to_pdf(st.session_state["cover_letter"])
    with open(pdf_cl, "rb") as f:
        st.download_button("⬇️ Download Cover Letter (PDF)", f.read(), file_name="cover_letter.pdf", mime="application/pdf")
