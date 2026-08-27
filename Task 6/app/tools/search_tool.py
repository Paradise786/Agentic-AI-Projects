import urllib.parse
from pydantic import BaseModel, Field
import requests
from app.tools.registry import BaseTool, tool_registry
from app.config import settings

class SearchSchema(BaseModel):
    query: str = Field(description="Search terms to lookup online (e.g. 'Agentic AI news' or 'python-telegram-bot release status')")

class SearchTool(BaseTool):
    name = "web_search"
    description = "Searches the web for news, definitions, and articles."
    input_schema = SearchSchema

    def _execute(self, args: SearchSchema, context: dict) -> str:
        query = args.query.strip()
        
        # If in Demo Mode, simulate search results
        if settings.DEMO_MODE:
            return self._simulate_search(query)

        try:
            # Use DuckDuckGo HTML parser search API as a lightweight open lookup
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=5.0)
            if r.status_code == 200:
                # Basic scraping to get the first few results text
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, 'html.parser')
                links = soup.find_all('a', class_='result__snippet')
                results = []
                for idx, link in enumerate(links[:3]):
                    results.append(f"Result {idx+1}: {link.get_text(strip=True)}")
                if results:
                    return "\n".join(results)
            return self._simulate_search(query)
        except Exception:
            return self._simulate_search(query)

    def _simulate_search(self, query: str) -> str:
        q_lower = query.lower()
        if "agentic ai" in q_lower:
            return """Simulated Web Search Results:
1. Agentic AI Overview: Agentic AI represents a class of systems that autonomously plan, execute, observe, and adjust tools to fulfill user intentions.
2. Design Patterns for Agents: Discusses Orchestrator-Worker, Planning-Validation, and memory patterns.
3. LangGraph & LangChain: Dynamic routing tools that govern node states in complex LLM chains."""
        elif "python-telegram-bot" in q_lower:
            return """Simulated Web Search Results:
1. python-telegram-bot v20+ Documentation: Explains the transition to asyncio-based handlers, ApplicationBuilder, and ContextTypes.
2. InlineKeyboards in Telegram: Tutorial on building CallbackQuery handlers for professional bot structures."""
        else:
            return f"Simulated Web Search Results for '{query}':\nFound 3 relevant articles summarizing information for '{query}'. Synthesizing topic details..."

# Auto register
tool_registry.register(SearchTool())
