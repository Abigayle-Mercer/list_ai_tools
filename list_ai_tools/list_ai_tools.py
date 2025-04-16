import importlib
import json
from typing import Any, Dict, Optional, List, Callable, Tuple
import jsonschema

# Minimal schema compatible with OpenAI function calling and LangChain-style tools
DEFAULT_TOOL_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^[a-zA-Z_][a-zA-Z0-9_]*$": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["object"]},
                        "properties": {"type": "object"},
                        "required": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["type", "properties"]
                }
            },
            "required": ["description", "parameters"]
        }
    }
}

# Flat registry: tool_name -> callable
CALLABLE_REGISTRY: Dict[str, Callable] = {}

def list_ai_tools(extension_manager, schema: Optional[dict] = None, return_metadata_only: bool = False
) -> List[Dict[str, Any]]:
    discovered_tools: List[Dict[str, Any]] = []
    validation_schema = schema if schema is not None else DEFAULT_TOOL_SCHEMA
    CALLABLE_REGISTRY.clear()

    for ext_name in extension_manager.extensions:
        try:
            module = importlib.import_module(ext_name)
            if hasattr(module, "jupyter_server_extension_tools"):
                func = getattr(module, "jupyter_server_extension_tools")
                if callable(func):
                    tools = func()
                    if isinstance(tools, dict):
                        for tool_name, tool_info in tools.items():
                            if isinstance(tool_info, dict) and "callable" in tool_info:
                                if tool_name in CALLABLE_REGISTRY:
                                    raise ValueError(f"Duplicate tool name detected: '{tool_name}'")

                                # Register callable
                                CALLABLE_REGISTRY[tool_name] = tool_info["callable"]

                                # Validate metadata against schema
                                jsonschema.validate(instance=tool_info["metadata"], schema=validation_schema)

                                if return_metadata_only:
                                    discovered_tools.append(tool_info["metadata"])
                                else:
                                    discovered_tools.append({tool_name: tool_info})

        except jsonschema.ValidationError as ve:
            discovered_tools.append({"error": f"Schema validation failed in '{ext_name}': {ve.message}"})
        except Exception as e:
            discovered_tools.append({"error": f"Error loading extension '{ext_name}': {str(e)}"})

    return discovered_tools

# ---- Parsers for tool call formats ----

def parse_standard_tool_call(call: Dict) -> Tuple[str, Dict]:
    return call.get("name"), call.get("arguments", {})

def parse_openai_tool_call(call: Dict) -> Tuple[str, Dict]:
    fn = call.get("function", {})
    name = fn.get("name")
    arguments = json.loads(fn.get("arguments", "{}"))
    return name, arguments

def parse_anthropic_tool_call(call: Dict) -> Tuple[str, Dict]:
    return call.get("name"), call.get("input", {})

# ---- Main tool execution logic ----

def run(tool_calls: List[Dict[str, Any]], parse_fn: Optional[Callable[[Dict], Tuple[str, Dict]]] = None) -> List[Any]:
    """
    Execute a sequence of tools from structured tool call objects.

    Parameters:
        tool_calls: List of tool call objects (varied format)
        parse_fn: A function to extract (name, arguments) from each call
            e.g. parse_standard_tool_call, parse_openai_tool_call, parse_anthropic_tool_call

    Returns:
        List of results from each tool
    """
    results = []
    if parse_fn is None:
        parse_fn = parse_standard_tool_call

    for call in tool_calls:
        tool_name, tool_args = parse_fn(call)

        if not tool_name:
            raise ValueError("Tool call did not include a valid 'name'.")

        try:
            func = CALLABLE_REGISTRY[tool_name]
        except KeyError:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")

        results.append(func(**tool_args))

    return results

