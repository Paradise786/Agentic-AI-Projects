import os
import requests
import json
import logging
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.demo_mode = settings.DEMO_MODE

    def check_health(self) -> bool:
        """Checks if the local Ollama instance is running."""
        if self.demo_mode:
            return True
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def query(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> str:
        """Sends a query to the configured Ollama LLM, with Demo Mode fallback."""
        if self.demo_mode or not self.check_health():
            if not self.demo_mode:
                logger.warning("Ollama is offline. Falling back to Demo Mode simulation.")
            return self._simulate_llm(prompt, system_prompt, json_mode)

        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            if system_prompt:
                payload["system"] = system_prompt
            if json_mode:
                payload["format"] = "json"

            response = requests.post(url, json=payload, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.error(f"Ollama returned status code {response.status_code}: {response.text}")
                return self._simulate_llm(prompt, system_prompt, json_mode)
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {str(e)}")
            return self._simulate_llm(prompt, system_prompt, json_mode)

    def _simulate_llm(self, prompt: str, system_prompt: Optional[str], json_mode: bool) -> str:
        """Simulates LLM outputs for various system and user prompts."""
        prompt_lower = prompt.lower()
        
        # 1. Intent Detection
        if "classify" in prompt_lower or "intent" in prompt_lower:
            return self._mock_intent(prompt_lower)

        # 2. Planner Agent
        if "plan" in prompt_lower and ("step" in prompt_lower or "workflow" in prompt_lower):
            return self._mock_plan(prompt_lower)

        # 3. Validation Agent
        if "validate" in prompt_lower or "verification" in prompt_lower:
            return self._mock_validation(prompt_lower)

        # 4. Data Analysis / Stats summary
        if "analyze" in prompt_lower and "csv" in prompt_lower:
            return self._mock_data_analysis(prompt_lower)

        # 5. Summarization & Document queries
        if "summarize" in prompt_lower or "summary" in prompt_lower:
            return self._mock_summarization(prompt_lower)

        # 6. Communication (Emails/Rewrite)
        if "email" in prompt_lower or "rewrite" in prompt_lower or "professional" in prompt_lower:
            return self._mock_communication(prompt_lower)

        # 7. RAG / Q&A from files
        if "document" in prompt_lower or "page" in prompt_lower or "fees" in prompt_lower or "pdf" in prompt_lower:
            return self._mock_rag(prompt_lower)

        # 8. Productivity / Tasks / Reminders
        if "task" in prompt_lower or "remind" in prompt_lower:
            return self._mock_productivity(prompt_lower)

        # Default fallback text
        if json_mode:
            return json.dumps({
                "response": "Acknowledged. Operating in simulated mode.",
                "status": "success"
            })
        return "I have processed your request. Operating in simulated environment mode."

    def _mock_intent(self, prompt: str) -> str:
        data = {
            "intent": "general",
            "confidence": 0.95,
            "requires_confirmation": False
        }
        if "task" in prompt:
            data["intent"] = "task_management"
        elif "remind" in prompt:
            data["intent"] = "reminder_management"
            if "tomorrow" not in prompt and "pm" not in prompt and "am" not in prompt:
                # Ambiguous time
                data["requires_confirmation"] = True
        elif "pdf" in prompt or "docx" in prompt or "document" in prompt or "read" in prompt:
            data["intent"] = "document_processing"
        elif "csv" in prompt or "analyze" in prompt:
            data["intent"] = "data_analysis"
        elif "search" in prompt or "find" in prompt or "research" in prompt:
            data["intent"] = "research"
        elif "remember" in prompt or "memory" in prompt or "forget" in prompt:
            data["intent"] = "memory_management"
        elif "email" in prompt or "write" in prompt or "rewrite" in prompt:
            data["intent"] = "communication"
        
        return json.dumps(data)

    def _mock_plan(self, prompt: str) -> str:
        steps = []
        if "pdf" in prompt or "document" in prompt:
            steps = [
                {"step": 1, "description": "Read and parse document structure", "tool": "pdf_reader", "agent": "Document Agent"},
                {"step": 2, "description": "Index textual contents into vector space", "tool": "rag_indexing", "agent": "RAG Agent"},
                {"step": 3, "description": "Analyze paragraphs and draft summary", "tool": "summarization_tool", "agent": "Document Agent"},
                {"step": 4, "description": "Identify and extract action items", "tool": "validation_tool", "agent": "Validation Agent"},
                {"step": 5, "description": "Save action items as tasks", "tool": "task_creator", "agent": "Productivity Agent"}
            ]
        elif "csv" in prompt or "analyze" in prompt:
            steps = [
                {"step": 1, "description": "Load and inspect CSV schema", "tool": "csv_analyzer", "agent": "Data Analysis Agent"},
                {"step": 2, "description": "Compute row counts and column stats", "tool": "csv_analyzer", "agent": "Data Analysis Agent"},
                {"step": 3, "description": "Detect data quality problems or patterns", "tool": "validation_tool", "agent": "Validation Agent"},
                {"step": 4, "description": "Synthesize summary explanation", "tool": "summarization_tool", "agent": "Data Analysis Agent"}
            ]
        elif "research" in prompt:
            steps = [
                {"step": 1, "description": "Search web for information", "tool": "web_search", "agent": "Research Agent"},
                {"step": 2, "description": "Collect and cross-reference articles", "tool": "summarization_tool", "agent": "Research Agent"},
                {"step": 3, "description": "Create task list for study guide", "tool": "task_creator", "agent": "Productivity Agent"}
            ]
        else:
            steps = [
                {"step": 1, "description": "Evaluate incoming parameter constraints", "tool": "datetime_tool", "agent": "Orchestrator Agent"},
                {"step": 2, "description": "Execute requested action", "tool": "calculator_tool", "agent": "Orchestrator Agent"},
                {"step": 3, "description": "Verify output meets formatting checks", "tool": "validation_tool", "agent": "Validation Agent"}
            ]
        return json.dumps({"steps": steps})

    def _mock_validation(self, prompt: str) -> str:
        status = "VALID"
        reason = "All required inputs are present, calculations or data inputs are formatted properly."
        
        if "reminder" in prompt or "remind" in prompt:
            if "time" in prompt or "at" in prompt:
                status = "VALID"
            else:
                status = "REQUIRES_CONFIRMATION"
                reason = "The reminder target time is missing or ambiguous."
        elif "task" in prompt and "title" not in prompt:
            status = "FAILED"
            reason = "A valid title must be supplied for the task."

        return json.dumps({
            "status": status,
            "reason": reason,
            "suggestions": ["Please clarify date/time format if needed"]
        })

    def _mock_data_analysis(self, prompt: str) -> str:
        return """📊 CSV Statistical Analysis
- Columns found: 'Date', 'Category', 'Amount', 'Status'
- Records analyzed: 120 rows
- Missing data: 'Status' columns has 12 empty cells.
- Pattern identified: Expenses are highest on Fridays. 'Amount' average value is 45.5.
- Validation: Success. File read completes."""

    def _mock_summarization(self, prompt: str) -> str:
        return """📚 Document Summary:
This document outlines the standard operation procedures for remote AI deployments. It covers configuration steps, local model parameters (like temperature, top-p settings), security tokens validation, and error recovery policies when endpoints drop offline.

Key action items:
1. Initialize local SQlite database connection.
2. Confirm vector similarity fallbacks work.
3. Schedule daily status alerts using APScheduler."""

    def _mock_communication(self, prompt: str) -> str:
        return """✉️ Generated Response:
Subject: Final Project Timeline Update

Dear Team,

Please note that the final submission deadline for the project has been updated to this coming Friday at 5:00 PM. Kindly ensure all tasks are validated, and the repository code is pushed prior to this time.

Best regards,
Assistant"""

    def _mock_rag(self, prompt: str) -> str:
        return """📄 Document Answer:
The standard fee structure dictates that standard accounts incur a 1.5% processing charge per invoice, whereas premium tier accounts do not have processing charges.

📚 Source:
file_sample.pdf (Page 3, Section 2)"""

    def _mock_productivity(self, prompt: str) -> str:
        return "I have recognized a productivity intent. Creating/updating the database entry successfully."

llm_service = LLMService()
