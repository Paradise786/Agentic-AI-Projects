# Core Agents 1-8 implementation
"""
CivicFlow AI - Core Agents 1-8
"""
import json
from schemas import (
    SuperAgentDecision, ProblemUnderstanding, EvidenceIntelligence,
    MemoryRetrievalResult, DuplicateCheck, CommunitySignal,
    GeoHotspotReport, PriorityScoring
)
from llm_config import get_groq_llm
from database import ticket_vector_collection

try:
    llm = get_groq_llm()
except Exception as e:
    print(f"Warning: Could not initialize ChatGroq: {e}")
    llm = None

# Agent 1: Super Agent Orchestrator
def run_master_orchestrator(raw_text: str) -> SuperAgentDecision:
    try:
        if llm is None:
            raise ValueError("LLM not initialized")
        structured_llm = llm.with_structured_output(SuperAgentDecision)
        prompt = f"Analyze complaint and give execution plan (Agents 2 to 8):\n{raw_text}"
        return structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Fallback triggered for run_master_orchestrator due to: {e}")
        return SuperAgentDecision(
            execution_plan=["Agent 2", "Agent 3", "Agent 4", "Agent 5", "Agent 6", "Agent 7", "Agent 8"],
            is_emergency="sewage" in raw_text.lower() or "rupture" in raw_text.lower() or "flood" in raw_text.lower(),
            reasoning="Fallback mode: detected potential infrastructure hazard from keywords."
        )

# Agent 2: Problem Intelligence Agent
def run_problem_intelligence(raw_text: str) -> ProblemUnderstanding:
    try:
        if llm is None:
            raise ValueError("LLM not initialized")
        structured_llm = llm.with_structured_output(ProblemUnderstanding)
        prompt = f"Categorize and extract severity for:\n{raw_text}"
        return structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Fallback triggered for run_problem_intelligence due to: {e}")
        text_lower = raw_text.lower()
        if "sewage" in text_lower or "sewer" in text_lower or "overflow" in text_lower:
            category, subcategory, severity = "Sanitation", "Sewer Overflow", "Critical"
        elif "water" in text_lower or "pipe" in text_lower or "leak" in text_lower:
            category, subcategory, severity = "Water Supply", "Pipe Leak", "High"
        elif "light" in text_lower or "electric" in text_lower or "power" in text_lower:
            category, subcategory, severity = "Power & Energy", "Streetlight Outage", "Medium"
        else:
            category, subcategory, severity = "General Municipal", "Other", "Low"
        return ProblemUnderstanding(
            category=category,
            subcategory=subcategory,
            risk_severity=severity,
            summary=raw_text[:100]
        )

# Agent 3: Evidence Intelligence Agent
def run_evidence_intelligence(image_description: str, text: str) -> EvidenceIntelligence:
    try:
        if llm is None:
            raise ValueError("LLM not initialized")
        structured_llm = llm.with_structured_output(EvidenceIntelligence)
        prompt = f"Compare text '{text}' with image evidence description '{image_description}'. Detect conflicts."
        return structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Fallback triggered for run_evidence_intelligence due to: {e}")
        return EvidenceIntelligence(
            visual_evidence_valid=bool(image_description),
            detected_objects=["flooding", "debris"] if "water" in text.lower() else ["general_hazard"],
            conflict_detected=False,
            confidence_score=0.85
        )

# Agent 4: Multi-Agent Memory Agent
def run_memory_agent(query_text: str) -> MemoryRetrievalResult:
    try:
        results = ticket_vector_collection.query(query_texts=[query_text], n_results=3)
        ids_list = results.get('ids', [[]])
        past_count = len(ids_list[0]) if ids_list else 0
    except Exception as e:
        print(f"Memory Agent ChromaDB query error: {e}")
        past_count = 0
    return MemoryRetrievalResult(
        similar_past_cases_count=past_count,
        recommended_strategy="Apply standard municipal patch repair strategy based on historical success."
    )

# Agent 5: Duplicate Intelligence Agent
def run_duplicate_check(text: str) -> DuplicateCheck:
    try:
        results = ticket_vector_collection.query(query_texts=[text], n_results=1)
        distances = results.get('distances', [[]])
        ids = results.get('ids', [[]])
        if distances and len(distances) > 0 and len(distances[0]) > 0 and distances[0][0] < 0.2:
            return DuplicateCheck(is_duplicate=True, existing_master_id=ids[0][0], similarity_score=0.95)
    except Exception as e:
        print(f"Duplicate Check ChromaDB error: {e}")
    return DuplicateCheck(is_duplicate=False, existing_master_id=None, similarity_score=0.1)

# Agent 6: Community Signal Agent
def run_community_signal(ticket_id: str, duplicate_count: int) -> CommunitySignal:
    impact = min(100, duplicate_count * 20 + 10)
    return CommunitySignal(community_impact_score=impact, master_incident_id=f"MASTER_{ticket_id}")

# Agent 7: Geo Predictive Hotspot Agent
def run_geo_hotspot(location_name: str) -> GeoHotspotReport:
    return GeoHotspotReport(hotspot_risk_score=78.5, cluster_area_name=location_name)

# Agent 8: Risk Priority Agent
def run_risk_priority(problem: ProblemUnderstanding, community: CommunitySignal) -> PriorityScoring:
    base_score = 30
    if problem.risk_severity.lower() == "critical":
        base_score += 40
    elif problem.risk_severity.lower() == "high":
        base_score += 25
    final_score = min(100, base_score + int(community.community_impact_score * 0.3))
    if final_score > 75:
        return PriorityScoring(final_risk_score=final_score, sla_target_hours=6, priority_level="P1-Emergency")
    return PriorityScoring(final_risk_score=final_score, sla_target_hours=24, priority_level="P2-High")
