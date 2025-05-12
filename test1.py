import streamlit as st
import openai

# Page title
st.title("🧠 Smart CV Tailoring Assistant")
st.markdown("""
Paste a job description and your full experience CV once.  
This app will extract key info, skills, experiences, ATS match, missing keywords, and a cover letter!
""")

# API Key input
openai_api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")

# Job Description Input
job_description = st.text_area("📄 Paste Full Job Description Here", height=300)

# CV Session Memory
if "saved_cv" not in st.session_state:
    st.session_state["saved_cv"] = ""

# Ask for CV only if not saved
if not st.session_state["saved_cv"]:
    full_cv_input = st.text_area("📘 Paste Your Full Experience CV Here", height=300)
    if full_cv_input:
        st.session_state["saved_cv"] = full_cv_input
        st.success("✅ CV saved for this session!")
else:
    st.markdown("✅ CV already saved for this session.")
    if st.button("❌ Clear CV"):
        st.session_state["saved_cv"] = ""
        st.experimental_rerun()

# Reuse saved CV
full_cv = st.session_state["saved_cv"]

# --- Functions ---

# 1. Extract structured fields from JD
def extract_structured_job_info(job_description, api_key):
    prompt = f"""
You are a professional career assistant.

Given the following job description, extract and clearly label these components:

1. About the Company
2. Role Summary / Responsibilities
3. Requirements
4. Experience Required
5. Skills (short bullet list of 1–2 word items)

Job Description:
{job_description}

Format the output like:

**About the Company:**  
...

**Role Summary / Responsibilities:**  
...

**Requirements:**  
...

**Experience Required:**  
...

**Skills:**  
- skill1  
- skill2  
...
all should be very brief
"""
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=600,
    )
    return response['choices'][0]['message']['content']

# 2. Extract ATS Skills + Expected Experience
def generate_from_jd(job_description, api_key):
    prompt = f"""
You are an expert career assistant.

Given the following Full Job Description:

{job_description}

Do the following:
1. Extract a **short list of SKILLS** (only 1-2 words each, no long sentences). Make it clean and ATS-friendly.
2. Write **three brief WORK EXPERIENCES** that the ideal candidate is expected to have (each 1-2 lines) using the STAR method.

Output exactly like this:

Skills:
- Group 1: skill1, skill2, skill3
- Group 2: skill1, skill2

Work Experiences:
1. [First expected experience]
2. [Second expected experience]
3. [Third expected experience]
"""
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=500,
    )
    return response['choices'][0]['message']['content']

# 3. ATS Match + Missing Keywords
def get_ats_match_and_missing_keywords(job_description, full_cv, api_key):
    prompt = f"""
You are an ATS expert.

Compare the job description and the candidate's full experience CV below.

Job Description:
{job_description}

Candidate CV:
{full_cv}

Tasks:
1. Estimate the ATS match percentage between the CV and the job description (based on experience, skill, education & keyword overlap).
2. List the important missing keywords or concepts from the CV that appear in the job description.

Output in this format:

**ATS Match:** XX%

**Missing Keywords:**
- keyword1
- keyword2
...
"""
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400,
    )
    return response['choices'][0]['message']['content']

# 4. Cover Letter Generator
def generate_cover_letter(job_description, full_cv, api_key):
    prompt = f"""
You are a professional cover letter writer.

Write a concise, personalized 3-paragraph cover letter based on the following job description and candidate CV. Focus on aligning strengths with the role.

Job Description:
{job_description}

Candidate CV:
{full_cv}
"""
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )
    return response['choices'][0]['message']['content']

# --- Run Button ---
if st.button("🚀 Run Tailoring Pipeline"):
    if openai_api_key and job_description and full_cv:
        with st.spinner("Processing everything..."):
            # Step 1: Extract structured job info
            structured_info = extract_structured_job_info(job_description, openai_api_key)

            # Step 2: Skills and expected experience
            skills_output = generate_from_jd(job_description, openai_api_key)

            # Step 3: ATS match & missing keywords
            ats_output = get_ats_match_and_missing_keywords(job_description, full_cv, openai_api_key)

            # Step 4: Generate cover letter
            cover_letter_output = generate_cover_letter(job_description, full_cv, openai_api_key)

        # Show results
        st.subheader("📂 Parsed Job Description")
        st.markdown(structured_info)

        st.subheader("✅ Extracted ATS Skills & Ideal Work Experiences")
        st.markdown(skills_output)

        st.subheader("📊 ATS Match and Missing Keywords")
        st.markdown(ats_output)

        st.subheader("✉️ Tailored Cover Letter")
        st.markdown(cover_letter_output)
    else:
        st.error("Please enter your API key, job description, and full CV (if not already saved).")
