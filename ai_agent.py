import os
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.utilities import DuckDuckGoSearchAPIWrapper
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

load_dotenv()

# 🔑 OpenAI API setup
llm = ChatOpenAI(
    model_name="o4-mini",  # Or o4-mini
    temperature=1
)

# 🧠 Memory
memory = ConversationBufferMemory(memory_key="chat_history")

# 🔧 Tools
def search_jobs(query: str) -> str:
    search = DuckDuckGoSearchAPIWrapper()
    results = search.run(query + " site:linkedin.com/jobs")
    return results


def scrape_job_titles(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        titles = [tag.get_text(strip=True) for tag in soup.find_all(["h1", "h2", "h3"])]
        return "\n".join(titles[:10]) if titles else "No titles found."
    except Exception as e:
        return f"Error scraping: {e}"


tools = [
    Tool(
        name="WebSearch",
        func=search_jobs,
        description="Search jobs from LinkedIn or job boards using a query.",
    ),
    Tool(
        name="ScrapeWebpage",
        func=scrape_job_titles,
        description="Scrape job titles from a URL.",
    ),
]

# 🤖 Initialize Agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
)
