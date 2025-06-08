from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory

# Define an LLM (OpenAI here, but you can swap)
llm = OpenAI(openai_api_key = "",temperature=0)

# Define a simple tool (for demo, just a calculator)
def calculator_tool(query: str) -> str:
    # dummy calculator response
    try:
        return str(eval(query))
    except:
        return "Invalid expression"

tools = [
    Tool(
        name="Calculator",
        func=calculator_tool,
        description="Useful for math calculations"
    )
]

# Set up conversation memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Initialize LangChain agent with tools, LLM, and memory
agent = initialize_agent(
    tools, 
    llm, 
    agent="zero-shot-react-description",  # simple agent type
    memory=memory,
    verbose=True
)

# Query the agent
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    response = agent.run(user_input)
    print("Agent:", response)
