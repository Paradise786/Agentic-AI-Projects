"""
CivicFlow AI - Extended Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional

# Example response schema for the orchestrator output
class TicketResponse(BaseModel):
    ticket_id: str = Field(description="Unique identifier for the incident ticket")
    status: str = Field(description="Current status of the ticket, e.g., 'Open', 'In Progress', 'Resolved'")
    priority: str = Field(description="Priority level assigned by the priority scoring agent")
    assigned_department: str = Field(description="Primary department responsible for handling the incident")
    recommended_actions: List[str] = Field(description="Step‑by‑step actions suggested by the resolution plan agent")
    estimated_cost_pkr: Optional[float] = Field(default=None, description="Estimated cost for remediation, if applicable")
    notes: Optional[str] = Field(default=None, description="Additional free‑form notes or comments")

# Additional schemas can be added here as the system grows
