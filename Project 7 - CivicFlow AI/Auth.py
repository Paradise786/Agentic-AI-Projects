import hashlib
from database import SessionLocal, UserModel
import streamlit as st

# ==========================================
# PASSWORD HASHING (PBKDF2 SHA256)
# ==========================================
SALT = "civicflow_secure_salt_2026"

def hash_password(plain_password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256"""
    if not plain_password:
        return ""
    return hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), SALT.encode('utf-8'), 100000).hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    if not plain_password or not hashed_password:
        return False
    computed = hash_password(plain_password)
    if computed == hashed_password:
        return True
    # Fallback check for plain text or sha256
    simple_sha = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    if simple_sha == hashed_password:
        return True
    return False


# ==========================================
# USER REGISTRATION
# ==========================================
def signup_user(email: str, password: str, role: str, full_name: str = ""):
    """
    Register new user
    Returns: (success: bool, message: str)
    """
    email_clean = str(email).strip().lower()
    if not email_clean or "@" not in email_clean:
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    clean_role = "Authority" if "auth" in str(role).lower() else ("Admin" if "admin" in str(role).lower() else "Citizen")
    db = SessionLocal()
    try:
        existing = db.query(UserModel).filter_by(email=email_clean).first()
        if existing:
            return False, "An account with this email already exists. Please sign in instead."
        user = UserModel(
            email=email_clean,
            hashed_password=hash_password(password),
            role=clean_role,
            full_name=full_name or email_clean.split("@")[0]
        )
        db.add(user)
        db.commit()
        return True, "Account created successfully. Please sign in."
    except Exception as e:
        db.rollback()
        return False, f"Registration failed: {str(e)}"
    finally:
        db.close()


# ==========================================
# USER LOGIN
# ==========================================
def login_user(email: str, password: str):
    """
    Authenticate user
    Returns: (success: bool, user_data: dict or message: str)
    """
    email_clean = str(email).strip().lower()
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter_by(email=email_clean).first()
        if not user:
            return False, "No account found with this email. Please sign up first."
        if not verify_password(password, user.hashed_password):
            return False, "Incorrect password."
        return True, {
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "id": user.id
        }
    finally:
        db.close()


# ==========================================
# STREAMLIT SESSION MANAGEMENT
# ==========================================
def init_session_state():
    """Initialize Streamlit session state for authentication"""
    defaults = {
        "authenticated": False,
        "user_role": None,
        "username": None,
        "user_email": None,
        "screen": "GetStarted",
        "selected_login_role": "Citizen"
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def logout_user():
    """Clear authentication session"""
    st.session_state["authenticated"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None
    st.session_state["user_email"] = None
    st.session_state["screen"] = "GetStarted"


def get_current_user():
    """Get current authenticated user data"""
    if not st.session_state.get("authenticated"):
        return None
    return {
        "email": st.session_state.get("user_email"),
        "role": st.session_state.get("user_role"),
        "username": st.session_state.get("username")
    }


def require_auth(roles: list = None):
    """
    Guard to ensure user is authenticated and optionally has required role(s).
    """
    if not st.session_state.get("authenticated"):
        st.session_state["screen"] = "GetStarted"
        st.rerun()
    if roles and st.session_state.get("user_role") not in roles:
        st.error("Access denied. Insufficient permissions.")
        st.stop()