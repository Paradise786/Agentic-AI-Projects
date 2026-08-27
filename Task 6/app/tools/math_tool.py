import re
from pydantic import BaseModel, Field
from app.tools.registry import BaseTool, tool_registry

class CalculatorSchema(BaseModel):
    expression: str = Field(description="Arithmetic expression to evaluate (e.g. '2 + 2' or '5 * 10 / 2')")

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Safely evaluate basic mathematical expressions."
    input_schema = CalculatorSchema

    def _execute(self, args: CalculatorSchema, context: dict) -> str:
        expr = args.expression
        # Restrict input expression to safe characters for security
        expr = re.sub(r'[^0-9+\-*/().\s]', '', expr)
        if not expr.strip():
            raise ValueError("Empty or invalid mathematical expression.")
        
        try:
            # Safe evaluation using basic arithmetic only
            result = eval(expr, {"__builtins__": None}, {})
            return str(result)
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {e}")

# Auto register
tool_registry.register(CalculatorTool())
