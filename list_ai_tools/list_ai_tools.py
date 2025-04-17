import importlib
import json
from typing import Any, Dict, Optional, List, Callable, Tuple
import jsonschema


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
                        "required": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["type", "properties"]
                },
                "callable": {}
            },
            "required": ["description", "parameters", "callable"]
        }
    }
}


def list_ai_tools(extension_manager, schema: Optional[dict] = None) -> List[Dict[str, Any]]:
    discovered_tools: List[Dict[str, Any]] = []
    validation_schema = schema if schema is not None else DEFAULT_TOOL_SCHEMA

    for ext_name in extension_manager.extensions:
        try:
            module = importlib.import_module(ext_name)
            if hasattr(module, "jupyter_server_extension_tools"):
                func = getattr(module, "jupyter_server_extension_tools")
                if callable(func):
                    tools = func()
                    print(tools)
                    # Validate full structure (including presence of callable)
                    jsonschema.validate(instance=tools, schema=validation_schema)

                    # Now ensure all callables are actually callable
                    #for name, tool_info in tools.items():
                    #    if not callable(tool_info.get("callable")):
                    #        raise TypeError(f"Tool '{name}' has a non-callable 'callable' field")
    
                    discovered_tools.append(tools)

        except (jsonschema.ValidationError, TypeError) as e:
            print({ext_name: {"error": f"Schema validation failed: {str(e)}"}})
        except Exception as e:
            print({ext_name: {"error": str(e)}})
    print(discovered_tools)
    return discovered_tools






