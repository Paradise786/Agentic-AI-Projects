import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def get_llm(model_name: str = None, temperature: float = 0.1):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in .env file.")
    
    if not model_name:
        model_name = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    
    return ChatGroq(
        model=model_name,
        temperature=temperature,
        max_retries=2,
        api_key=groq_api_key
    )

# Global instance
llm = get_llm()
get_groq_llm = get_llm
