from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReminderBase(BaseModel):
    text: str
    target_time: datetime
    is_recurring: bool = False
    cron_expr: Optional[str] = None
    status: str = "active"

class ReminderCreate(ReminderBase):
    pass

class ReminderResponse(ReminderBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MemoryBase(BaseModel):
    key: str
    value: str

class MemoryCreate(MemoryBase):
    pass

class MemoryResponse(MemoryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ToolCallSchema(BaseModel):
    tool_name: str
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ExecutionLogResponse(BaseModel):
    id: str
    user_id: int
    request: str
    intent: Optional[str] = None
    plan: Optional[Any] = None
    selected_agent: Optional[str] = None
    selected_tools: Optional[Any] = None
    validation_result: Optional[str] = None
    duration: float
    status: str
    timestamp: datetime
    tool_calls: List[ToolCallSchema] = []

    class Config:
        from_attributes = True

class SystemStatusResponse(BaseModel):
    telegram_bot: str
    ollama: str
    database: str
    vector_store: str
    scheduler: str
    storage: str
    agent_engine: str
    details: dict

class DashboardMetrics(BaseModel):
    total_users: int
    conversations: int
    tasks: int
    reminders: int
    documents: int
    agent_executions: int
    successful_runs: int
    failed_runs: int
