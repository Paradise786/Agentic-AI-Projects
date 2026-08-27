from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from llm_config import llm

class ProblemUnderstanding(BaseModel):
    summary: str = Field(description="1 line summary of complaint")
    urgency: str = Field(description="Low, Medium, High, or Emergency")

class ClassificationResult(BaseModel):
    department: str = Field(description="Water, Sanitation, Electricity, Roads, Parks, Emergency")
    confidence: float = Field(description="0.0 to 1.0 confidence score")

class RiskAssessment(BaseModel):
    risk_level: str = Field(description="Low, Medium, High")
    sla_hours: int = Field(description="Hours required for resolution")

def analyze_complaint(text: str) -> ProblemUnderstanding:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Analyze municipal complaint."),
        ("human", "{text}")
    ])
    return (prompt | llm.with_structured_output(ProblemUnderstanding)).invoke({"text": text})

def classify_complaint(text: str) -> ClassificationResult:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Classify into: Water, Sanitation, Electricity, Roads, Parks, Emergency."),
        ("human", "{text}")
    ])
    return (prompt | llm.with_structured_output(ClassificationResult)).invoke({"text": text})

def assess_risk(text: str, dept: str) -> RiskAssessment:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Assess risk and SLA."),
        ("human", "Dept: {dept}\nComplaint: {text}")
    ])
    return (prompt | llm.with_structured_output(RiskAssessment)).invoke({"dept": dept, "text": text})
