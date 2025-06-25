import streamlit as st
from ai_agent import agent

st.set_page_config(page_title="AI Job Agent", layout="wide")
st.title("🤖 AI Job Agent with OpenAI (o4-mini Compatible)")

st.markdown(
    "### Example prompts:\n"
    "- Find AI jobs in London on LinkedIn\n"
    "- Search for Data Scientist jobs in UK\n"
    "- Find remote NLP roles on job boards"
)

query = st.text_input("💡 Enter your request", value="Find AI jobs in London on LinkedIn")

if st.button("Run AI Agent"):
    with st.spinner("🤖 Agent is thinking..."):
        output = agent.run(query)
    st.success("✅ Done!")
    st.markdown("### 🔍 Result:")
    st.write(output)
