import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")


def filter_relevant_jobs(job_titles, role_filter="AI, ML, Data Science, NLP"):
    prompt = f"""
You are an AI job filtering assistant. Your task is to look at the following list of job titles and select ONLY those that are related to {role_filter}.
Return the titles as a Python list.

Job Titles:
{job_titles}
"""
    try:
        response = openai.ChatCompletion.create(
            model="o4-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )
        answer = response['choices'][0]['message']['content']
        filtered = eval(answer) if answer.startswith("[") else []
        return filtered
    except Exception as e:
        return [f"OpenAI Error: {str(e)}"]
