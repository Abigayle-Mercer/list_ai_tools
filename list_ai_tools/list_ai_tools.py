import importlib
import json
from typing import Any, Dict, Optional, List, Callable, Tuple
import jsonschema


MCP_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["object"]},
                "properties": {"type": "object"},
                "required": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["type", "properties"]
        },
        "annotations": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "readOnlyHint": {"type": "boolean"},
                "destructiveHint": {"type": "boolean"},
                "idempotentHint": {"type": "boolean"},
                "openWorldHint": {"type": "boolean"}
            },
            "additionalProperties": True
        }
    },
    "required": ["name", "inputSchema"],
    "additionalProperties": False
}



def list_ai_tools(extension_manager, schema: Optional[dict] = None, return_metadata_only: bool = True
) -> List[Dict[str, Any]]:
    discovered_tools: List[Dict[str, Any]] = []
    validation_schema = schema if schema is not None else MCP_TOOL_SCHEMA

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
                                if tool_name in discovered_tools:
                                    raise ValueError(f"Duplicate tool name detected: '{tool_name}'")

                                # Validate metadata against schema
                                jsonschema.validate(instance=tool_info["metadata"], schema=validation_schema)

                                if return_metadata_only:
                                    discovered_tools.append(tool_info["metadata"])
                                else:
                                    discovered_tools.append({tool_name: tool_info})

        except jsonschema.ValidationError as ve:
            print({"error": f"Schema validation failed in '{ext_name}': {ve.message}"})
        except Exception as e:
            print({"error": f"Error loading extension '{ext_name}': {str(e)}"})

    return discovered_tools

# ---- Parsers for tool call formats ----

def parse_openai_tool_call(call: Dict) -> Tuple[str, Dict]:
    fn = call.get("function", {})
    name = fn.get("name")
    arguments = json.loads(fn.get("arguments", "{}"))
    return name, arguments

def parse_anthropic_tool_call(call: Dict) -> Tuple[str, Dict]: 
    return call.get("name"), call.get("input", {})

def parse_mcp_tool_call(call: Dict) -> Tuple[str, Dict]:
    return call.get("name"), call.get("input", {})

def parse_vercel_tool_call(call: Dict) -> Tuple[str, Dict]:
    return call.get("name"), call.get("arguments", {})

PARSER_MAP = {
    "openai": parse_openai_tool_call,
    "anthropic": parse_mcp_tool_call,
    "mcp": parse_mcp_tool_call,
    "vercel": parse_vercel_tool_call,
}


# keep writing these for popular LLMS 

# ---- Main tool execution logic ----

async def run(extension_manager,
    tool_calls: List[Dict[str, Any]],
    parse_fn: Optional[str | Callable[[Dict], Tuple[str, Dict]]] = None
) -> List[Any]:
    """
    Execute a sequence of tools from structured tool call objects.

    Parameters:
        tool_calls: List of tool call objects (varied format)
        parse_fn: Either a string (e.g. "openai", "mcp") or a function to extract (name, arguments) from each call

    Returns:
        List of results from each tool, including error messages if applicable
    """
    # Resolve parser
    if isinstance(parse_fn, str):
        if parse_fn not in PARSER_MAP:
            return [{"error": f"Unknown parser '{parse_fn}'. Valid parsers: {list(PARSER_MAP.keys())}"}]
        parse_fn = PARSER_MAP[parse_fn]
    elif parse_fn is None:
        parse_fn = PARSER_MAP["mcp"]

    # Build a local tool registry at runtime
    callable_registry = {}
    tool_groups = list_ai_tools(
        extension_manager,
        return_metadata_only=False
    )
    for group in tool_groups:
        for name, tool_def in group.items():
            callable_registry[name] = tool_def["callable"]

    results = []
    for i, call in enumerate(tool_calls):
        try:
            name, args = parse_fn(call)
            if name not in callable_registry:
                raise ValueError(f"Tool '{name}' not found in any extension.")

            fn = callable_registry[name]
            if asyncio.iscoroutinefunction(fn):
                result = await fn(**args)
            else:
                result = fn(**args)
            results.append(result)

        except Exception as e:
            results.append({
                "error": f"Tool call #{i + 1} failed: {str(e)}",
                "call": call
            })

    return results
