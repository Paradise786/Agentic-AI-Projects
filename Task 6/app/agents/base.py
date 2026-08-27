"""Base classes for all AI agents used in the Telegram Agentic Assistant.
These classes provide a minimal contract: a `run` method that takes a `context`
(dict) and returns a result dict. Agents can be stateful via injected services
(database sessions, LLM service, tool registry, etc.) and may update the shared
`execution_log` dictionary for later persistence.
"""

import abc
import uuid
import datetime
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BaseAgent(abc.ABC):
    """Abstract base for all agents.

    Sub‑classes must define a ``name`` attribute and implement ``run``.
    ``run`` receives a mutable ``context`` dict which contains keys such as
    ``user_id``, ``request``, ``conversation_id`` etc. It returns a dict with
    optional ``output`` and ``next_step`` fields for orchestration.
    """

    name: str = "base"

    def __init__(self, **services):
        # Services like db session, llm_service, tool_registry can be injected.
        self.services = services
        self.execution_id = str(uuid.uuid4())
        self.start_time = datetime.datetime.utcnow()
        logger.info(f"Agent {self.name} instantiated with execution id {self.execution_id}")

    @abc.abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent.

        Parameters
        ----------
        context: dict
            Mutable execution context.
        Returns
        -------
        dict
            May contain ``output`` (string) and ``next_step`` (agent name) to
            guide the orchestrator.
        """
        raise NotImplementedError

    def _log_step(self, step_name: str, details: Dict[str, Any]):
        """Helper to record a step inside the execution log.

        The orchestrator is responsible for persisting the final log record.
        """
        logger.debug(f"Agent {self.name} step '{step_name}': {details}")

    def finish(self, context: Dict[str, Any], status: str = "SUCCESS"):
        """Mark the agent as finished, record duration and status.
        """
        duration = (datetime.datetime.utcnow() - self.start_time).total_seconds()
        context.setdefault("execution_log", {})[self.execution_id] = {
            "agent": self.name,
            "status": status,
            "duration": duration,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        logger.info(f"Agent {self.name} finished with status {status} after {duration:.2f}s")
