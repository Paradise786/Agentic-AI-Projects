"""
CivicFlow AI - Pydantic Structured Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SuperAgentDecision(BaseModel):
    execution_plan: List[str] = Field(description="List of agent names to execute")
    is_emergency: bool = Field(description="Fast-track flag for critical safety issues")
    reasoning: str

class ProblemUnderstanding(BaseModel):
    category: str
    subcategory: str
    risk_severity: str = Field(description="Low, Medium, High, Critical")
    summary: str

class EvidenceIntelligence(BaseModel):
    visual_evidence_valid: bool
    detected_objects: List[str]
    conflict_detected: bool
    confidence_score: float

class MemoryRetrievalResult(BaseModel):
    similar_past_cases_count: int
    recommended_strategy: str

class DuplicateCheck(BaseModel):
    is_duplicate: bool
    existing_master_id: Optional[str] = None
    similarity_score: float

class CommunitySignal(BaseModel):
    community_impact_score: int
    master_incident_id: str

class GeoHotspotReport(BaseModel):
    hotspot_risk_score: float
    cluster_area_name: str

class PriorityScoring(BaseModel):
    final_risk_score: int
    sla_target_hours: int
    priority_level: str

class CivicRAG(BaseModel):
    applicable_sop: str
    required_equipment: List[str]

class DepartmentRouting(BaseModel):
    primary_agency: str
    secondary_agencies: List[str]

class ResolutionPlan(BaseModel):
    steps: List[str]
    estimated_cost_pkr: float

class ReviewerAudit(BaseModel):
    approved: bool
    audit_feedback: str

class HITLApprovalClassification(BaseModel):
    requires_human_approval: bool
    escalation_reason: Optional[str] = None

class EscalationStatus(BaseModel):
    current_tier: str
    sla_breached: bool

class ResolutionVerification(BaseModel):
    work_completed: bool
    quality_score: float

class DepartmentResourceOverview(BaseModel):
    department_name: str
    available_capacity_percentage: float

class CityHealthAssessment(BaseModel):
    overall_health_index: float
    executive_summary: str

class SmartCommunicationResult(BaseModel):
    channel: str
    sent_status: bool

class AutonomousCommandCenterReport(BaseModel):
    ticket_id: str
    final_status: str
    execution_summary: str
