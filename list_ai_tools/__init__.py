"""An extension to aggregate and expose the tools from all available jupyter extensions."""
from .extension import Extension
from .list_ai_tools import list_ai_tools, run, parse_standard_tool_call, parse_openai_tool_call, parse_anthropic_tool_call

__version__ = "0.1.0"


def _jupyter_server_extension_points():
    return [{
        "module": "list_ai_tools",
        "app": Extension
    }]
