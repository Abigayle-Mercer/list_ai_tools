import importlib
import json
from typing import Any, Dict, Optional, List, Callable, Tuple
import jsonschema

def list_ai_tools(extension_manager) -> dict:
    discovered_tools: List[Dict[str, Any]] = []

    for ext_name in extension_manager.extensions:
        try:
            module = importlib.import_module(ext_name)
            if hasattr(module, "jupyter_server_extension_tools"):
                func = getattr(module, "jupyter_server_extension_tools")
                if callable(func):
                    tools = func()
                    discovered_tools.append(tools)
        except Exception as e:
            print({ext_name: {"error": str(e)}})

    return discovered_tools
