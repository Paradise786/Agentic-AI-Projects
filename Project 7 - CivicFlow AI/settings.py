"""
CivicFlow AI — central settings & constants.
=============================================
Poori app ka **single source of truth**. Pehle SLA hours, department list aur
thresholds teen-chaar files mein duplicate the; ab sirf yahan hain.

Koi bhi module `from settings import ...` kar sakta hai. Yahan koi heavy import
nahi hai (na streamlit, na langchain) taake ye file har jagah safe rahe.
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple

# ----------------------------------------------------------
# .env load (agar python-dotenv mojood ho)
# ----------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv na ho to environment variables phir bhi kaam karti hain
    pass


def _env(key: str, default: str = "") -> str:
    return (os.getenv(key) or default).strip()


def _env_bool(key: str, default: bool = False) -> bool:
    raw = _env(key, str(default)).lower()
    return raw in ("1", "true", "yes", "on")


def _env_float(key: str, default: float) -> float:
    try:
        return float(_env(key, str(default)))
    except ValueError:
        return default


def _env_int(key: str, default: int) -> int:
    try:
        return int(float(_env(key, str(default))))
    except ValueError:
        return default


# ==========================================================
# 1. APP IDENTITY
# ==========================================================
APP_NAME = "CivicFlow AI"
APP_TAGLINE = "Agentic Municipal Complaint Intelligence"
APP_VERSION = "2.0.0"

# ==========================================================
# 2. LLM CONFIG
# ==========================================================
GROQ_API_KEY = _env("GROQ_API_KEY")
LLM_MODEL = _env("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = _env_float("LLM_TEMPERATURE", 0.2)

GOOGLE_API_KEY = _env("GOOGLE_API_KEY")
GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-1.5-flash")

# Placeholder values jo "key set hai" nahi maane jayenge
_PLACEHOLDER_KEYS = {
    "", "your_groq_api_key_here", "your-api-key", "changeme",
    "sk-xxx", "gsk_xxx", "none", "null",
}


def has_groq_key() -> bool:
    return GROQ_API_KEY.lower() not in _PLACEHOLDER_KEYS


def has_gemini_key() -> bool:
    return GOOGLE_API_KEY.lower() not in _PLACEHOLDER_KEYS


def has_any_llm_key() -> bool:
    return has_groq_key() or has_gemini_key()


# ==========================================================
# 3. ENGINE BEHAVIOUR
# ==========================================================
# LLM na ho to rule-based mode chale (magar UI par saaf label ke sath)
ALLOW_DEGRADED_MODE = _env_bool("ALLOW_DEGRADED_MODE", True)

# Critic agent is se kam confidence de to HITL / retry
CRITIC_CONFIDENCE_THRESHOLD = _env_float("CRITIC_CONFIDENCE_THRESHOLD", 0.7)

# Reflection loop guard — is se zyada retry nahi (infinite loop se bachao)
MAX_AGENT_RETRIES = _env_int("MAX_AGENT_RETRIES", 2)

# Chroma cosine similarity is se ooper = duplicate complaint
DUPLICATE_SIMILARITY_THRESHOLD = _env_float("DUPLICATE_SIMILARITY_THRESHOLD", 0.85)

# Structured output validation fail ho to itni dafa repair prompt bhejein
MAX_VALIDATION_REPAIRS = _env_int("MAX_VALIDATION_REPAIRS", 2)

# ==========================================================
# 4. OBSERVABILITY
# ==========================================================
LANGCHAIN_TRACING_V2 = _env_bool("LANGCHAIN_TRACING_V2", False)
LANGCHAIN_API_KEY = _env("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = _env("LANGCHAIN_PROJECT", "civicflow-ai")
LANGCHAIN_ENDPOINT = _env("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# ==========================================================
# 5. STORAGE
# ==========================================================
DATABASE_URL = _env("DATABASE_URL", "sqlite:///./civicflow.db")
CHROMA_DB_PATH = _env("CHROMA_DB_PATH", "./chroma_store")
LANGGRAPH_CHECKPOINT_PATH = _env(
    "LANGGRAPH_CHECKPOINT_PATH", "./checkpoints/civicflow_checkpoints.sqlite"
)
TICKET_COLLECTION = "civic_ticket_memory"
SOP_COLLECTION = "municipal_sops"

# ==========================================================
# 6. EXTERNAL TOOLS
# ==========================================================
OPENWEATHER_API_KEY = _env("OPENWEATHER_API_KEY")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
TOOL_HTTP_TIMEOUT = 8  # seconds


def has_weather_key() -> bool:
    return OPENWEATHER_API_KEY.lower() not in _PLACEHOLDER_KEYS


# ==========================================================
# 7. MUNICIPAL DOMAIN — departments (whitelist)
# ==========================================================
# Guardrail: LLM sirf in agencies mein se chun sakta hai. Kuch aur de to
# reject + HITL flag. Ye "LLM ko blindly trust na karna" ka concrete example hai.

DEPARTMENTS: Dict[str, Dict[str, object]] = {
    "WASA Water Supply": {
        "code": "WASA",
        "scope": "Water supply, pipelines, sewerage, drainage, sewer overflow",
        "keywords": ["water", "pipe", "pipeline", "sewage", "sewer", "drain", "drainage",
                     "leak", "leakage", "tap", "supply", "flood", "flooding"],
        "contact": "wasa.helpline@civicflow.gov.pk",
    },
    "LESCO Electricity Board": {
        "code": "LESCO",
        "scope": "Electricity distribution, transformers, feeders, exposed wiring",
        "keywords": ["electricity", "electric", "power", "transformer", "wire", "wiring",
                     "cable", "pole", "kv", "shock", "sparking", "outage", "load"],
        "contact": "lesco.complaints@civicflow.gov.pk",
    },
    "LWMC Solid Waste": {
        "code": "LWMC",
        "scope": "Solid waste collection, garbage dumps, street sweeping",
        "keywords": ["waste", "garbage", "trash", "dump", "rubbish", "kachra",
                     "sweeping", "bin", "litter"],
        "contact": "lwmc.waste@civicflow.gov.pk",
    },
    "C&W Road Infrastructure": {
        "code": "C&W",
        "scope": "Roads, potholes, pavements, bridges, footpaths",
        "keywords": ["road", "pothole", "pavement", "footpath", "bridge", "street",
                     "asphalt", "manhole", "speed breaker"],
        "contact": "cw.roads@civicflow.gov.pk",
    },
    "CDA Sanitation": {
        "code": "CDA",
        "scope": "Public sanitation, toilets, hygiene, mosquito spraying",
        "keywords": ["sanitation", "hygiene", "toilet", "washroom", "spray",
                     "fumigation", "cleanliness", "stagnant"],
        "contact": "cda.sanitation@civicflow.gov.pk",
    },
    "SSGC Gas Infrastructure": {
        "code": "SSGC",
        "scope": "Gas pipelines, meters, gas leakage emergencies",
        "keywords": ["gas", "cylinder", "meter", "smell", "lpg", "gas leak"],
        "contact": "ssgc.gas@civicflow.gov.pk",
    },
    "Traffic Police": {
        "code": "TRAFFIC",
        "scope": "Traffic signals, illegal parking, road obstruction, signage",
        "keywords": ["traffic", "signal", "parking", "obstruction", "congestion",
                     "encroachment", "zebra", "sign"],
        "contact": "traffic.control@civicflow.gov.pk",
    },
    "Health Department": {
        "code": "HEALTH",
        "scope": "Public health hazards, dengue, disease outbreak, food safety",
        "keywords": ["health", "dengue", "malaria", "disease", "outbreak", "clinic",
                     "hospital", "food", "epidemic", "mosquito"],
        "contact": "health.dept@civicflow.gov.pk",
    },
    "Street Lighting Authority": {
        "code": "LIGHTS",
        "scope": "Street lights, park lighting, dark spots",
        "keywords": ["light", "streetlight", "street light", "lamp", "dark", "bulb"],
        "contact": "lighting@civicflow.gov.pk",
    },
    "Rescue 1122": {
        "code": "RESCUE",
        "scope": "Fire, building collapse, rescue emergencies, immediate danger",
        "keywords": ["fire", "collapse", "explosion", "rescue", "trapped", "blast",
                     "emergency", "smoke"],
        "contact": "rescue1122@civicflow.gov.pk",
    },
}

DEPARTMENT_NAMES: List[str] = list(DEPARTMENTS.keys())
DEFAULT_DEPARTMENT = "WASA Water Supply"


def is_valid_department(name: str) -> bool:
    """Guardrail helper — LLM ka diya department approved list mein hai ya nahi."""
    return name in DEPARTMENTS


def resolve_department(name: str) -> str:
    """LLM ka jawab whitelist par snap karein: exact → case-insensitive → code → default."""
    if not name:
        return DEFAULT_DEPARTMENT
    cleaned = name.strip()
    if cleaned in DEPARTMENTS:
        return cleaned
    lowered = cleaned.lower()
    for dept, meta in DEPARTMENTS.items():
        if dept.lower() == lowered or str(meta["code"]).lower() == lowered:
            return dept
    for dept in DEPARTMENTS:
        if dept.lower() in lowered or lowered in dept.lower():
            return dept
    return DEFAULT_DEPARTMENT


# ==========================================================
# 8. PRIORITY / SLA MATRIX (single source of truth)
# ==========================================================
# Pehle SLA hours orchestrator_pipeline.py aur app.py dono mein hardcoded the.
# Ab sirf yahan. Guardrail bhi isi se validate karta hai.

PRIORITY_LEVELS: List[str] = ["Low", "Medium", "High", "Critical"]

SLA_MATRIX: Dict[str, Dict[str, object]] = {
    "Critical": {"sla_hours": 2,  "risk_floor": 85, "color": "#dc2626", "tier": "Tier 3 — Emergency Cell"},
    "High":     {"sla_hours": 12, "risk_floor": 65, "color": "#ea580c", "tier": "Tier 2 — Zonal Officer"},
    "Medium":   {"sla_hours": 24, "risk_floor": 40, "color": "#ca8a04", "tier": "Tier 1 — Field Team"},
    "Low":      {"sla_hours": 72, "risk_floor": 0,  "color": "#16a34a", "tier": "Tier 1 — Field Team"},
}

ALLOWED_SLA_HOURS = {int(v["sla_hours"]) for v in SLA_MATRIX.values()}


def sla_hours_for(priority: str) -> int:
    return int(SLA_MATRIX.get(priority, SLA_MATRIX["Medium"])["sla_hours"])


def priority_for_risk(risk_score: int) -> str:
    """Risk score (0-100) se priority derive karein — consistent mapping."""
    score = max(0, min(100, int(risk_score)))
    for level in ("Critical", "High", "Medium", "Low"):
        if score >= int(SLA_MATRIX[level]["risk_floor"]):
            return level
    return "Low"


def priority_color(priority: str) -> str:
    return str(SLA_MATRIX.get(priority, SLA_MATRIX["Medium"])["color"])


# ==========================================================
# 9. TICKET STATUS LIFECYCLE
# ==========================================================
STATUS_FLOW: List[str] = [
    "PENDING", "AWAITING_APPROVAL", "DISPATCHED", "IN_PROGRESS", "RESOLVED", "REJECTED",
]

STATUS_META: Dict[str, Dict[str, str]] = {
    "PENDING":           {"label": "Pending Triage",    "color": "#64748b", "icon": "🕒"},
    "AWAITING_APPROVAL": {"label": "Awaiting Approval", "color": "#7c3aed", "icon": "🛡️"},
    "DISPATCHED":        {"label": "Dispatched",        "color": "#0ea5e9", "icon": "📤"},
    "IN_PROGRESS":       {"label": "In Progress",       "color": "#ca8a04", "icon": "🔧"},
    "RESOLVED":          {"label": "Resolved",          "color": "#16a34a", "icon": "✅"},
    "REJECTED":          {"label": "Rejected",          "color": "#dc2626", "icon": "🚫"},
}

# ==========================================================
# 10. ISSUE CATEGORIES (wizard step 3 + classifier ke liye)
# ==========================================================
ISSUE_CATEGORIES: Dict[str, List[str]] = {
    "💧 Water & Sewerage": [
        "Pipeline burst / leakage", "No water supply", "Contaminated water",
        "Sewer overflow", "Blocked drain", "Street flooding",
    ],
    "⚡ Electricity": [
        "Power outage", "Exposed / fallen wire", "Transformer fault",
        "Sparking pole", "Voltage fluctuation",
    ],
    "🗑️ Solid Waste": [
        "Garbage not collected", "Illegal dump site", "Overflowing bin",
        "Street not swept",
    ],
    "🛣️ Roads & Infrastructure": [
        "Pothole", "Broken pavement / footpath", "Open manhole",
        "Damaged bridge / culvert", "Missing road sign",
    ],
    "🧼 Sanitation & Health": [
        "Public toilet unusable", "Mosquito breeding / stagnant water",
        "Dengue hotspot", "Food safety concern", "Dead animal on road",
    ],
    "🔥 Gas & Emergency": [
        "Gas leakage", "Fire hazard", "Building collapse risk", "Explosion risk",
    ],
    "🚦 Traffic & Encroachment": [
        "Traffic signal not working", "Illegal parking", "Road obstruction",
        "Illegal encroachment",
    ],
    "💡 Street Lighting": [
        "Street light not working", "Dark spot / safety concern", "Park lighting fault",
    ],
}


def flat_categories() -> List[str]:
    out: List[str] = []
    for group, items in ISSUE_CATEGORIES.items():
        for item in items:
            out.append(f"{group} — {item}")
    return out


# ==========================================================
# 11. GEO REFERENCE (locations → coordinates)
# ==========================================================
LOCATION_COORDS: Dict[str, Tuple[float, float]] = {
    "Layyah City Center":       (30.9693, 70.9428),
    "Chowk Azam, Layyah":       (30.9333, 71.0333),
    "Karor Lal Esan, Layyah":   (31.2226, 70.9498),
    "Layyah":                   (30.9693, 70.9428),
    "Model Town, Lahore":       (31.4805, 74.3239),
    "Gulberg, Lahore":          (31.5204, 74.3587),
    "DHA Lahore":               (31.4697, 74.3980),
    "Lahore":                   (31.5204, 74.3587),
    "F-7 Islamabad":            (33.7215, 73.0531),
    "G-10 Islamabad":           (33.6844, 73.0180),
    "Islamabad":                (33.6844, 73.0479),
    "Clifton Karachi":          (24.8138, 67.0300),
    "North Nazimabad Karachi":  (24.9333, 67.0392),
    "Karachi":                  (24.8607, 67.0011),
    "Hayatabad Peshawar":       (33.9870, 71.4395),
    "Peshawar":                 (34.0151, 71.5249),
    "Other Location":           (30.9693, 70.9428),
}

DEFAULT_LOCATION = "Layyah City Center"

# Pakistan-wide map view
COUNTRY_CENTER = {"lat": 30.3753, "lon": 69.3451}
COUNTRY_ZOOM = 5
CITY_ZOOM = 12
PINPOINT_ZOOM = 13


def get_location_coords(location_name: str) -> Tuple[float, float]:
    """Location naam se (lat, lon).

    Tarteeb: (1) exact match, (2) known area ka naam input ke andar mile to sab se
    lamba (specific) match, (3) input kisi known naam ka hissa ho to sab se chhota
    (city-level) match, (4) default.
    """
    if not location_name:
        return LOCATION_COORDS[DEFAULT_LOCATION]

    if location_name in LOCATION_COORDS:
        return LOCATION_COORDS[location_name]

    lowered = str(location_name).strip().lower()
    if not lowered:
        return LOCATION_COORDS[DEFAULT_LOCATION]

    contained = [k for k in LOCATION_COORDS if k.lower() in lowered]
    if contained:
        return LOCATION_COORDS[max(contained, key=len)]

    partial = [k for k in LOCATION_COORDS if lowered in k.lower()]
    if partial:
        return LOCATION_COORDS[min(partial, key=len)]

    return LOCATION_COORDS[DEFAULT_LOCATION]


WIZARD_LOCATIONS: List[str] = [
    "Layyah City Center",
    "Chowk Azam, Layyah",
    "Karor Lal Esan, Layyah",
    "Model Town, Lahore",
    "Gulberg, Lahore",
    "DHA Lahore",
    "F-7 Islamabad",
    "G-10 Islamabad",
    "Clifton Karachi",
    "North Nazimabad Karachi",
    "Hayatabad Peshawar",
    "Other Location",
]

# ==========================================================
# 12. GUARDRAIL LIMITS
# ==========================================================
MIN_DESCRIPTION_CHARS = 15
MAX_DESCRIPTION_CHARS = 2000
MIN_DESCRIPTION_WORDS = 3
MAX_RISK_SCORE = 100
MIN_RISK_SCORE = 0
