import requests
from bs4 import BeautifulSoup
def extract_jobs(url, use_selenium=False):
    if use_selenium:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        import time

        def init_driver():
            options = Options()
            options.add_argument("--headless")
            return webdriver.Chrome(options=options)

        jobs = []
        try:
            driver = init_driver()
            driver.get(url)
            time.sleep(5)
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                text = link.text.strip()
                if any(k in text.lower() for k in ['engineer', 'data', 'ai', 'ml', 'developer', 'scientist']):
                    jobs.append(text)
        except Exception as e:
            jobs = [f"Selenium Error: {str(e)}"]
        finally:
            driver.quit()
        return list(set(jobs))

    # Fallback to Requests
    jobs = []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a'):
            text = link.get_text(strip=True)
            if any(k in text.lower() for k in ['engineer', 'data', 'ai', 'ml', 'developer', 'scientist']):
                jobs.append(text)
    except Exception as e:
        jobs = [f"Requests Error: {str(e)}"]

    return list(set(jobs))
