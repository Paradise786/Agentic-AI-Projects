"""
CivicFlow AI - Intelligent Municipal Chatbot Engine (FINAL FIX)
"""
import re
from typing import Optional, Any

# LLM import (Make sure this matches your llm_config.py)
try:
    from llm_config import llm
except Exception:
    llm = None

def generate_citizen_response(username: str, user_msg: str, latest_ticket: Optional[Any] = None) -> str:
    """Generate precise, helpful municipal response using intent matching + Real LLM."""
    msg = user_msg.strip()
    msg_clean = msg.lower()
    uname = (username or "Citizen").split("@")[0].replace(".", " ").title()

    # 1. GREETING INTENT
    if re.search(r'\b(hy|hi|hello|hey|salam|assalam|aoa|greetings|morning|evening)\b', msg_clean):
        return (
            f"👋 Hello {uname}! Welcome to CivicFlow AI Assistant. Main aapki kya madad kar sakta hoon?\n\n"
            f"Aap mujhse pooch sakte hain:\n"
            f"- 📷 Photo / evidence upload karne ka tareeqa\n"
            f"- 🏢 Complaint kis department ko assign hui hai\n"
            f"- 🎫 Submitted ticket ka live status check karna\n"
            f"- 🤖 System architecture ya technical sawal"
        )

    # 2. TICKET STATUS & TRACKING INTENT
    if re.search(r'\b(status|ticket|tracking|progress|kahan tak|check|update|kya bana|case|cf-)\b', msg_clean):
        if latest_ticket:
            t_id = getattr(latest_ticket, 'ticket_id', 'CF-XXXX')
            loc = getattr(latest_ticket, 'location', 'N/A')
            agency = getattr(latest_ticket, 'assigned_agency', 'Pending Assignment')
            stat = getattr(latest_ticket, 'status', 'PENDING')
            prio = getattr(latest_ticket, 'priority_level', 'Medium')
            return (
                f"🎫 **Aapki Latest Ticket Status Details:**\n\n"
                f"- **Ticket ID:** {t_id}\n"
                f"- **Location:** {loc}\n"
                f"- **Assigned Department:** {agency}\n"
                f"- **Current Status:** **{stat}**\n"
                f"- **Priority:** {prio}\n\n"
                f"Complete list dekhne ke liye aap sidebar se **'📋 My Tickets'** tab par visit kar sakte hain."
            )
        return (
            f"📭 **No Active Ticket Found:**\n\n"
            f"Aap ke account par filhal koi active complaint submit nahi hui. Nayi ticket submit karne ke liye "
            f"sidebar se **'🚀 Report Issue'** par jayein."
        )

    # 3. PHOTO / EVIDENCE UPLOAD INTENT
    if re.search(r'\b(photo|tasveer|picture|image|evidence|upload|attach|attatch|file|pdf|audio)\b', msg_clean):
        return (
            f"📷 **Photo & Evidence Upload:**\n\n"
            f"Haan bilkul! Aap complaint submit karte waqt Step 4 (**Add Evidence**) par tasveer (JPG/PNG), "
            f"audio recording, ya PDF document upload kar sakte hain.\n\n"
            f"CivicFlow AI ka **Evidence Verification Agent** aap ki image ko cross-verify karta hai aur "
            f"foran relevant department (WASA, LESCO, LWMC, etc.) ko attach karke forward karta hai."
        )

    # 4. DEPARTMENT ASSIGNMENT / ROUTING INTENT
    if re.search(r'\b(department|dept|agency|assigned|routing|kis ko|kis ke|koun dekhega|kahan jaya|kis dept)\b', msg_clean):
        if latest_ticket and getattr(latest_ticket, 'assigned_agency', None):
            dept_name = latest_ticket.assigned_agency
            t_id = getattr(latest_ticket, 'ticket_id', 'Active Ticket')
            loc = getattr(latest_ticket, 'location', 'Your Area')
            return (
                f"🏢 **Department Assignment Info:**\n\n"
                f"Aapki latest complaint (**{t_id}** - {loc}) **{dept_name}** ko assign ki gayi hai.\n\n"
                f"CivicFlow AI ka **Adaptive SLA Router** complaint ki text aur category ke mutabiq automatic "
                f"department route karta hai (Water issues -> **WASA**, Electricity -> **LESCO/PESCO**, "
                f"Sanitation -> **LWMC/CDA**, Roads -> **C&W Road Infrastructure**)."
            )
        return (
            f"🏢 **Department Assignment Info:**\n\n"
            f"CivicFlow AI ka **Adaptive SLA Router** maslay ki type ke mutabiq automatic relevant department assign karta hai:\n\n"
            f"- 💧 **Water & Sewage:** WASA Water Supply\n"
            f"- ⚡ **Electricity & Wires:** LESCO / PESCO Electricity Board\n"
            f"- 🛣️ **Potholes & Roads:** C&W Road Infrastructure\n"
            f"- 🗑️ **Garbage & Cleanliness:** LWMC / CDA Sanitation\n\n"
            f"Aap kisi bhi submitted ticket ka assigned department **'📋 My Tickets'** section mein dekh sakte hain."
        )

    # 5. EVERYTHING ELSE -> SEND TO REAL GROQ LLM (Technical & Complex Questions)
    if llm:
        try:
            system_prompt = (
                "You are CivicFlow AI, an expert municipal assistant. "
                "Answer the user's question accurately based on the CivicFlow AI system architecture. "
                "Key technical facts to use if asked: "
                "1. Duplicate detection uses ChromaDB vector embeddings and cosine similarity (>0.85 threshold). "
                "2. Workflow is managed by LangGraph StateGraph with conditional edges. "
                "3. Classification and Risk Assessment use Groq LLM (llama-3.3-70b) with Pydantic structured outputs. "
                "4. Guardrails module handles input validation and prompt injection protection. "
                "Keep the answer concise, helpful, and in a natural mix of Roman Urdu and English."
            )
            res = llm.invoke(f"{system_prompt}\n\nUser Question: {user_msg}")
            if hasattr(res, "content") and res.content:
                return str(res.content)
            return str(res)
        except Exception as e:
            return f"🤖 AI is temporarily busy. Please try again. (Error: {e})"

    # 6. FALLBACK (if LLM is not configured)
    return (
        f"🤖 **CivicFlow AI Assistant:**\n\n"
        f"Main aap ki municipal complaints, photo/evidence upload, ticket tracking aur department assignment mein poori madad kar sakta hoon.\n\n"
        f"Aap mujhse apni ticket ka status, department details ya issue reporting ke baray mein sawal pooch sakte hain!"
    )
