"""
CivicFlow AI – Database Engine
SQLAlchemy ORM with SQLite backend.
ChromaDB is optional and loaded lazily to prevent startup errors.
"""
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# DATABASE CONFIGURATION
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./civicflow.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==========================================
# SQLALCHEMY MODELS
# ==========================================
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    tickets = relationship("TicketModel", back_populates="citizen", foreign_keys="TicketModel.citizen_id")


class TicketModel(Base):
    __tablename__ = "tickets"
    ticket_id = Column(String, primary_key=True, index=True)
    citizen_id = Column(String, ForeignKey("users.email"), index=True, nullable=True)
    raw_text = Column(Text, nullable=True)
    image_description = Column(String, nullable=True)
    resolution_image = Column(String, nullable=True)
    location = Column(String, nullable=True)
    latitude = Column(String, nullable=True)
    longitude = Column(String, nullable=True)
    assigned_agency = Column(String, nullable=True)
    priority_level = Column(String, nullable=True)
    risk_score = Column(Integer, default=50)
    risk_reasons = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    status = Column(String, nullable=True, default="PENDING")
    is_hitl_flagged = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)
    rating = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    citizen = relationship("UserModel", back_populates="tickets", foreign_keys=[citizen_id])
    audit_logs = relationship("AgentAuditLog", back_populates="ticket")


class NotificationModel(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String, index=True, nullable=False)
    ticket_id = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    notification_type = Column(String, default="INFO")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentAuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, index=True)
    ticket_id = Column(String, ForeignKey("tickets.ticket_id"), index=True, nullable=True)
    agent_name = Column(String, nullable=True)
    node_name = Column(String, nullable=True)
    action_taken = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ticket = relationship("TicketModel", back_populates="audit_logs")


# Create all tables
Base.metadata.create_all(bind=engine)


# ==========================================
# OPTIONAL CHROMADB (lazy load)
# ==========================================
ticket_vector_collection = None
sop_vector_collection = None

try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_store")
    _chroma_client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )
    ticket_vector_collection = _chroma_client.get_or_create_collection(
        name="ticket_memory",
        metadata={"hnsw:space": "cosine"},
    )
    sop_vector_collection = _chroma_client.get_or_create_collection(
        name="municipal_sops",
        metadata={"hnsw:space": "cosine"},
    )
except Exception:
    # ChromaDB not available — vector features disabled, core app still works
    pass


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_user(email: str, hashed_password: str, role: str, full_name: str = None):
    db = SessionLocal()
    try:
        user = UserModel(email=email, hashed_password=hashed_password, role=role, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_user_by_email(email: str):
    db = SessionLocal()
    try:
        return db.query(UserModel).filter(UserModel.email == email).first()
    finally:
        db.close()


def create_ticket(ticket_data: dict):
    db = SessionLocal()
    try:
        ticket = TicketModel(**ticket_data)
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_ticket_by_id(ticket_id: str):
    db = SessionLocal()
    try:
        return db.query(TicketModel).filter(TicketModel.ticket_id == ticket_id).first()
    finally:
        db.close()


def get_tickets_by_citizen(citizen_id: str):
    db = SessionLocal()
    try:
        return db.query(TicketModel).filter(TicketModel.citizen_id == citizen_id).all()
    finally:
        db.close()


def update_ticket_status(ticket_id: str, status: str):
    db = SessionLocal()
    try:
        ticket = db.query(TicketModel).filter(TicketModel.ticket_id == ticket_id).first()
        if ticket:
            ticket.status = status
            db.commit()
            db.refresh(ticket)
        return ticket
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def create_audit_log(log_data: dict):
    db = SessionLocal()
    try:
        log = AgentAuditLog(**log_data)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_audit_logs_by_ticket(ticket_id: str):
    db = SessionLocal()
    try:
        return (
            db.query(AgentAuditLog)
            .filter(AgentAuditLog.ticket_id == ticket_id)
            .order_by(AgentAuditLog.timestamp.desc())
            .all()
        )
    finally:
        db.close()


def create_notification(user_email: str, message: str, ticket_id: str = None, notification_type: str = "INFO"):
    db = SessionLocal()
    try:
        notif = NotificationModel(
            user_email=user_email,
            ticket_id=ticket_id,
            message=message,
            notification_type=notification_type,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def get_user_notifications(user_email: str, limit: int = 20):
    db = SessionLocal()
    try:
        return (
            db.query(NotificationModel)
            .filter(NotificationModel.user_email == user_email)
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def mark_notifications_read(user_email: str):
    db = SessionLocal()
    try:
        db.query(NotificationModel).filter(NotificationModel.user_email == user_email).update({"is_read": True})
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def submit_ticket_rating(ticket_id: str, rating: int, feedback: str = ""):
    db = SessionLocal()
    try:
        ticket = db.query(TicketModel).filter(TicketModel.ticket_id == ticket_id).first()
        if ticket:
            ticket.rating = rating
            ticket.feedback = feedback
            db.commit()
            db.refresh(ticket)
        return ticket
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()