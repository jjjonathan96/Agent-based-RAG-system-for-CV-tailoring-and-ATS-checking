import streamlit as st
import openai

# Setup your OpenAI key (or use local LLM API if you have)
openai.api_key = st.secrets["OPENAI_API_KEY"]
def generate_skills_and_experience(company, role, expectation):
    prompt = f"""
You are a career expert. 
Given the following:

About Company:
{company}

About Role:
{role}

Role Expectation:
{expectation}

1. Extract a short list of grouped SKILLS (example groups: 'Deep Learning and ML', 'Cloud & DevOps', etc.).
2. Write two brief WORK EXPERIENCES that the ideal candidate is expected to have (each 2-3 lines).

Return in this format:

Skills:
- Group 1: skill1, skill2, skill3
- Group 2: skill1, skill2

Work Experiences:
1. [First work experience]
2. [Second work experience]
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return response['choices'][0]['message']['content']

# Streamlit App
st.title("Job Skills & Experience Extractor")

st.subheader("Enter Job Description Details")
company = st.text_area("About Company")
role = st.text_area("About Role")
expectation = st.text_area("Role Expectation")

if st.button("Generate Skills & Experience"):
    if company and role and expectation:
        output = generate_skills_and_experience(company, role, expectation)
        st.markdown(output)
    else:
        st.error("Please fill in all sections!")
