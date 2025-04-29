import streamlit as st
import openai

# Set Streamlit page
st.title("Job Description → Skills & Expected Experience Extractor")
st.markdown("Paste the full job description below. I'll extract skills (for ATS) and two expected experiences!")

# 1. API Key Input
openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")

# 2. Paste Job Description
job_description = st.text_area("Paste Full Job Description Here", height=300)

# Function to generate Skills & Work Experience
def generate_from_jd(job_description, api_key):
    prompt = f"""
You are an expert career assistant.

Given the following Full Job Description:

{job_description}

Do the following:
1. Extract a **short list of SKILLS** (only 1-2 words each, no long sentences).  Make it clean and ATS-friendly.
2. Write **three brief WORK EXPERIENCES** that the ideal candidate is expected to have (each 1-2 lines) should be like star method.

Output exactly like this:

Skills:
- Group 1: skill1, skill2, skill3
- Group 2: skill1, skill2

Work Experiences:
1. [First expected experience]
2. [Second expected experience]
"""

    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=500,
    )
    return response['choices'][0]['message']['content']

# 3. Button to run
if st.button("Extract Skills & Experience"):
    if openai_api_key and job_description:
        with st.spinner("Extracting, please wait..."):
            output = generate_from_jd(job_description, openai_api_key)
            st.markdown(output)
    else:
        st.error("Please enter both API key and Job Description.")
