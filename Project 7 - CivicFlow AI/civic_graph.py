import json
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from llm_config import llm
from guardrails import validate_complaint
from pydantic import BaseModel, Field

# ----------------------------------------------------
# State schema (lightweight for this demo)
# ----------------------------------------------------
class ComplaintState(BaseModel):
    complaint: str = Field(..., description="Raw user complaint")
    user_email: str = Field(..., description="Full email of the reporter")
    department: str = ""
    classification: str = ""
    risk_level: str = ""
    summary: str = ""
    is_safe: bool = True
    rejection_reason: str | None = None

# ----------------------------------------------------
# Helper to get a structured LLM call
# ----------------------------------------------------
def llm_structured(schema: BaseModel):
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser

    parser = JsonOutputParser(pydantic_object=schema)
    prompt = PromptTemplate(
        template="""
        You are an expert municipal AI. Read the user's complaint and output JSON that matches the schema below.
        Only output valid JSON – no extra text.
        {format_instructions}
        """,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    return prompt | llm | parser

# ----------------------------------------------------
# Nodes
# ----------------------------------------------------
def intake_node(state: ComplaintState) -> Dict[str, Any]:
    guard = validate_complaint(state.complaint)
    if not guard.is_safe:
        return {
            "is_safe": False,
            "rejection_reason": guard.rejection_reason,
            "department": "Rejected",
            "risk_level": "N/A",
        }
    return {"is_safe": True}

def classify_node(state: ComplaintState) -> Dict[str, Any]:
    class Schema(BaseModel):
        department: str = Field(..., description="One of the DEPARTMENTS defined in settings")
        classification: str = Field(..., description="Short human‑readable label")
    out = llm_structured(Schema).invoke({"complaint": state.complaint})
    return {"department": out.department, "classification": out.classification}

def risk_node(state: ComplaintState) -> Dict[str, Any]:
    class Schema(BaseModel):
        risk_level: str = Field(..., description="Low, Medium, or High")
    out = llm_structured(Schema).invoke({"complaint": state.complaint, "department": state.department})
    return {"risk_level": out.risk_level}

def summary_node(state: ComplaintState) -> Dict[str, Any]:
    class Schema(BaseModel):
        summary: str = Field(..., description="One‑sentence TL;DR of the complaint")
    out = llm_structured(Schema).invoke({
        "complaint": state.complaint,
        "department": state.department,
        "risk_level": state.risk_level,
    })
    return {"summary": out.summary}

def final_node(state: ComplaintState) -> Dict[str, Any]:
    return {
        "department": state.department,
        "classification": state.classification,
        "risk_level": state.risk_level,
        "summary": state.summary,
        "is_safe": state.is_safe,
        "rejection_reason": state.rejection_reason,
    }

# ----------------------------------------------------
# Build graph
# ----------------------------------------------------
def build_graph():
    checkpointer = MemorySaver()
    graph = StateGraph(ComplaintState, checkpoint=checkpointer)
    graph.add_node("intake", intake_node)
    graph.add_node("classify", classify_node)
    graph.add_node("risk", risk_node)
    graph.add_node("summary", summary_node)
    graph.add_node("final", final_node)
    graph.set_entry_point("intake")
    graph.add_conditional_edges(
        "intake",
        lambda s: "safe" if s.is_safe else "unsafe",
        {"safe": "classify", "unsafe": END},
    )
    graph.add_edge("classify", "risk")
    graph.add_edge("risk", "summary")
    graph.add_edge("summary", "final")
    graph.add_edge("final", END)
    return graph.compile()

civic_agent = build_graph()
