from pydantic import BaseModel, validator
from typing import Optional

class InputGuardrails(BaseModel):
    """Validate incoming complaints before sending to LLM"""
    text: str
    is_safe: bool
    rejection_reason: Optional[str] = None

    @validator('text')
    def check_length(cls, v):
        if len(v.strip()) < 15:
            raise ValueError("Complaint bohot choti hai (minimum 15 characters).")
        if len(v) > 2000:
            raise ValueError("Complaint bohot lambi hai (maximum 2000 characters).")
        return v

    @validator('text')
    def check_prompt_injection(cls, v):
        dangerous_patterns = [
            "ignore previous instructions",
            "system prompt",
            "<<<",
            ">>>",
            "act as a system administrator",
            "jailbreak",
        ]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError("Security Alert: Invalid input pattern detected.")
        return v

def validate_complaint(complaint_text: str) -> InputGuardrails:
    """Validate complaint and return InputGuardrails.
    `is_safe` indicates whether the input passed validation.
    """
    try:
        return InputGuardrails(text=complaint_text, is_safe=True)
    except ValueError as e:
        return InputGuardrails(text=complaint_text, is_safe=False, rejection_reason=str(e))

# Alias for legacy name used elsewhere
validate_complaint_input = validate_complaint
