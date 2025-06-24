import openai
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

def filter_relevant_jobs(jobs, role_filter="AI, ML, LLM"):
    joined_text = "\n".join(jobs)
    prompt = f"""
Given the following job list, filter and return only those that are relevant to the following fields: {role_filter}.
Jobs:\n{joined_text}
Only return relevant job titles.
"""
    try:
        res = openai.ChatCompletion.create(
            model="o4-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
        )
        filtered_jobs = res.choices[0].message.content.strip().split('\n')
        return filtered_jobs
    except Exception as e:
        return [f"OpenAI Error: {str(e)}"]
