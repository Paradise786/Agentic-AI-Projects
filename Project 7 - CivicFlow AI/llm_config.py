import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def get_llm(model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.1):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in .env file.")
    
    return ChatGroq(
        model=model_name,
        temperature=temperature,
        max_retries=2,
        api_key=groq_api_key
    )

# Global instance
llm = get_llm()
