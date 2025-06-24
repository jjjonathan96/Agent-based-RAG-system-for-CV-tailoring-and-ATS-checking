# app.py
import streamlit as st
from crawler import extract_jobs
from utils import filter_relevant_jobs

st.set_page_config(page_title="AI Job Agent", layout="wide")
st.title("🧠 AI Job Agent: Scrape & Filter Jobs per Company")

companies_input = st.text_area("Enter Companies and Career URLs (format: Company,URL)", height=300, value="""TCS,https://www.tcs.com/careers
CTS,https://careers.cognizant.com/global/en
Infosys,https://www.infosys.com/careers/apply.html
Wipro,https://careers.wipro.com/careers-home/
JP Morgan,https://careers.jpmorgan.com/global/en/home
KPMG,https://home.kpmg/xx/en/home/careers.html
PwC,https://www.pwc.co.uk/careers.html
Sainsbury,https://sainsburys.jobs/
Barclays Bank,https://search.jobs.barclays/
Lloyds Bank,https://www.lloydsbankinggroup.com/careers/
EY,https://www.ey.com/en_uk/careers
Computershare,https://www.computershare.com/careers
NHS,https://www.jobs.nhs.uk/
NHS Digital,https://digital.nhs.uk/about-nhs-digital/careers""")

search_keywords = st.text_input("Enter job keywords to filter (e.g., AI, ML, Data Scientist)", value="AI, ML, Data Scientist, NLP")

if st.button("🔍 Scrape and Show Jobs"):
    company_list = []
    for line in companies_input.splitlines():
        try:
            name, url = line.strip().split(",")
            company_list.append((name.strip(), url.strip()))
        except:
            st.warning(f"Invalid line skipped: {line}")

    st.subheader("Results by Company")
    tabs = st.tabs([c[0] for c in company_list])

    for i, (company_name, company_url) in enumerate(company_list):
        with tabs[i]:
            st.markdown(f"🔗 [Career Page]({company_url})")
            raw_jobs = extract_jobs(company_url)
            raw_titles = [job[0] for job in raw_jobs if isinstance(job, (list, tuple)) and len(job) == 2]
            filtered_jobs = filter_relevant_jobs(raw_titles, role_filter=search_keywords)

            if not filtered_jobs:
                st.info("No relevant jobs found.")
            else:
                for title in filtered_jobs:
                    # Try to match title to full (title, link) pair
                    match = next((job for job in raw_jobs if isinstance(job, (list, tuple)) and len(job) == 2 and job[0] == title), None)
                    job_url = match[1] if match else ""
                    if job_url and job_url.startswith("/"):
                        job_url = company_url.rstrip("/") + job_url
                    if job_url:
                        st.markdown(f"- [{title}]({job_url})")
                    else:
                        st.write(f"- {title}")
