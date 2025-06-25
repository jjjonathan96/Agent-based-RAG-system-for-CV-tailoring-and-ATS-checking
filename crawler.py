from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time


def extract_linkedin_jobs(job="Data Scientist", location="London"):
    url = f"https://www.linkedin.com/jobs/search/?keywords={job}&location={location}"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    jobs = []
    try:
        driver.get(url)
        time.sleep(5)  # Wait for page to load

        job_cards = driver.find_elements(By.CLASS_NAME, 'job-card-list__title')

        for card in job_cards:
            title = card.text.strip()
            link = card.get_attribute('href')
            if title and link:
                jobs.append((title, link))

    except Exception as e:
        jobs.append((f"Error: {str(e)}", ""))
    finally:
        driver.quit()

    return jobs