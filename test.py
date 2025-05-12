import streamlit as st
import openai

# Set Streamlit page
st.title("Job Description → Skills, ATS Match, and Cover Letter Generator")
st.markdown("Paste the full job description and your full experience CV below. Get skills, expected experience, ATS match %, missing keywords, and a cover letter!")

# API Key Input
openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")

# Inputs
job_description = st.text_area("Paste Full Job Description Here", height=300)
full_cv = st.text_area("Paste Your Full Experience CV Here", height=300)

# Function: Extract Skills & Work Experiences
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
        temperature=0.5,
        max_tokens=500,
    )
    return response['choices'][0]['message']['content']

# Function: ATS Match and Missing Keywords
def get_ats_match_and_missing_keywords(job_description, full_cv, api_key):
    prompt = f"""
You are an ATS expert.

Compare the job description and the candidate's full experience CV below.

Job Description:
{job_description}

Candidate CV:
{full_cv}

Tasks:
1. Estimate the ATS match percentage between the CV and the job description (based on skill & keyword overlap).
2. List the important missing keywords or concepts from the CV that appear in the job description.

Output in this format:

ATS Match: XX%
Missing Keywords:
- keyword1
- keyword2
- ...
"""
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )
    return response['choices'][0]['message']['content']

# Function: Cover Letter Generator
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

# Run Button
if st.button("Run All"):
    if openai_api_key and job_description and full_cv:
        with st.spinner("Processing..."):
            skills_output = generate_from_jd(job_description, openai_api_key)
            ats_output = get_ats_match_and_missing_keywords(job_description, full_cv, openai_api_key)
            cover_letter_output = generate_cover_letter(job_description, full_cv, openai_api_key)

        st.subheader("✅ Extracted Skills & Expected Experience")
        st.markdown(skills_output)

        st.subheader("📊 ATS Match & Missing Keywords")
        st.markdown(ats_output)

        st.subheader("✉️ Cover Letter")
        st.markdown(cover_letter_output)
    else:
        st.error("Please enter your API key, job description, and full experience CV.")
