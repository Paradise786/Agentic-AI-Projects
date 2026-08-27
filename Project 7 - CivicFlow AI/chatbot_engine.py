"""
CivicFlow AI - Intelligent Municipal Chatbot Engine
"""

import re
from typing import Optional, Any

try:
    from llm_config import get_groq_llm
except Exception:
    get_groq_llm = None


def generate_citizen_response(username: str, user_msg: str, latest_ticket: Optional[Any] = None) -> str:
    """Generate precise, helpful municipal response using intent matching."""
    msg = user_msg.strip()
    msg_clean = msg.lower()
    uname = (username or "Citizen").split("@")[0].replace(".", " ").title()

    # 1. PHOTO / EVIDENCE UPLOAD INTENT
    if re.search(r'\b(photo|tasveer|picture|image|evidence|upload|attach|attatch|file|pdf|audio)\b', msg_clean):
        return (
            f"📷 **Photo & Evidence Upload:**\n\n"
            f"Haan bilkul! Aap complaint submit karte waqt Step 4 (**Add Evidence**) par tasveer (JPG/PNG), "
            f"audio recording, ya PDF document upload kar sakte hain.\n\n"
            f"CivicFlow AI ka **Evidence Verification Agent** aap ki image ko cross-verify karta hai aur "
            f"foran relevant department (WASA, LESCO, LWMC, etc.) ko attach karke forward karta hai."
        )

    # 2. DEPARTMENT ASSIGNMENT / ROUTING INTENT
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

    # 3. TICKET STATUS & TRACKING INTENT
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

    # 4. REPORTING PROCESS INTENT
    if re.search(r'\b(kaise|how to|report|tarika|tareeqa|method|darj|submit|problem|masla)\b', msg_clean):
        return (
            f"💡 **Civic Issue Report Karne Ka Tareeqa:**\n\n"
            f"1. Sidebar se **'🚀 Report Issue'** select karein.\n"
            f"2. **Location** chunein (Layyah, Lahore, Islamabad, Karachi, Peshawar etc.).\n"
            f"3. Problem ki detail description likhein.\n"
            f"4. Specific **Category** select karein (Water, Electricity, Roads, Garbage).\n"
            f"5. Tasveer/Evidence attach karke **Submit to CivicFlow AI** dabayein!"
        )

    # 5. GREETING INTENT (WITH STRICT WORD BOUNDARIES)
    if re.search(r'\b(hy|hi|hello|hey|salam|assalam|aoa|greetings|morning|evening)\b', msg_clean):
        return (
            f"👋 Hello {uname}! Welcome to CivicFlow AI Assistant. Main aapki kya madad kar sakta hoon?\n\n"
            f"Aap mujhse pooch sakte hain:\n"
            f"- 📷 Photo / evidence upload karne ka tareeqa\n"
            f"- 🏢 Complaint kis department ko assign hui hai\n"
            f"- 🎫 Submitted ticket ka live status check karna"
        )

    # 6. TRY GROQ LLM IF CONFIGURED
    if get_groq_llm:
        try:
            llm = get_groq_llm()
            res = llm.invoke(user_msg)
            if hasattr(res, "content") and res.content:
                return str(res.content)
            return str(res)
        except Exception:
            pass

    # 7. NATURAL FALLBACK RESPONSE
    return (
        f"🤖 **CivicFlow AI Assistant:**\n\n"
        f"Main aap ki municipal complaints, photo/evidence upload, ticket tracking aur department assignment mein poori madad kar sakta hoon.\n\n"
        f"Aap mujhse apni ticket ka status, department details ya issue reporting ke baray mein sawal pooch sakte hain!"
    )
