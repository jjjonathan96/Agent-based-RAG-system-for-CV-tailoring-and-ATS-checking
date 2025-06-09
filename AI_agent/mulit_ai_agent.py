from .base_agent import AIAgent

class CVTailoringAgent(AIAgent):
    def handle_query(self, query):
        # Use RAG, LLM to tailor CV based on query
        # Update memory/knowledge accordingly
        pass


class ChatAgent(AIAgent):
    def handle_query(self, query):
        # Use memory, changes, converstation base on query
        # Update memory/knowledge accordingly
        pass