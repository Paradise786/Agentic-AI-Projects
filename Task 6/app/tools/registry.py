import logging
from typing import Dict, Any, Callable, Type
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class BaseTool:
    name: str
    description: str
    input_schema: Type[BaseModel]

    def __init__(self):
        if not hasattr(self, 'name') or not hasattr(self, 'description') or not hasattr(self, 'input_schema'):
            raise NotImplementedError("Tool subclasses must define name, description, and input_schema attributes.")

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validates arguments against input_schema, executes the tool logic, and handles exceptions."""
        context = context or {}
        
        # 1. Parameter Validation
        try:
            validated_args = self.input_schema(**arguments)
        except ValidationError as e:
            logger.error(f"Validation failed for tool '{self.name}': {e}")
            return {
                "success": False,
                "error": f"Invalid arguments: {e.errors()}",
                "result": None
            }

        # 2. Tool Execution
        try:
            result = self._execute(validated_args, context)
            return {
                "success": True,
                "error": None,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing tool '{self.name}': {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "result": None
            }

    def _execute(self, args: BaseModel, context: Dict[str, Any]) -> Any:
        """Internal execution method to be overridden by child tools."""
        raise NotImplementedError("Subclasses must implement the _execute method.")

class ToolRegistry:
    def __init__(self):
        self._registry: Dict[str, BaseTool] = {}
        self._success_counts: Dict[str, int] = {}
        self._execution_counts: Dict[str, int] = {}
        self._last_used: Dict[str, str] = {}

    def register(self, tool: BaseTool):
        """Registers a tool instance."""
        self._registry[tool.name] = tool
        self._success_counts[tool.name] = 0
        self._execution_counts[tool.name] = 0
        self._last_used[tool.name] = "Never"
        logger.info(f"Tool '{tool.name}' registered successfully.")

    def get_tool(self, name: str) -> BaseTool:
        """Retrieves a registered tool by name."""
        return self._registry.get(name)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """Returns details on all registered tools for monitoring UI."""
        tools_list = {}
        for name, tool in self._registry.items():
            executions = self._execution_counts.get(name, 0)
            successes = self._success_counts.get(name, 0)
            rate = (successes / executions * 100) if executions > 0 else 100.0
            
            tools_list[name] = {
                "description": tool.description,
                "input_schema": tool.input_schema.model_json_schema(),
                "executions": executions,
                "success_rate": f"{rate:.1f}%",
                "last_used": self._last_used.get(name, "Never"),
                "status": "Healthy"
            }
        return tools_list

    def execute_tool(self, name: str, arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Looks up a tool, registers metadata stats, and triggers run()."""
        import datetime
        
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found in registry.",
                "result": None
            }

        self._execution_counts[name] += 1
        self._last_used[name] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        res = tool.run(arguments, context)
        
        if res["success"]:
            self._success_counts[name] += 1
        return res

tool_registry = ToolRegistry()
