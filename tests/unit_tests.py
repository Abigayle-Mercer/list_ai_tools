import sys
import io
import contextlib
import pytest
from types import SimpleNamespace
from list_ai_tools.list_ai_tools import list_ai_tools

# --- Setup Helper ---

def setup_module_with_tools(name, tools_func):
    sys.modules[name] = SimpleNamespace(jupyter_server_extension_tools=tools_func)

# --- Unit Tests ---

def test_single_valid_tool():
    def tools():
        return {
            "echo": {
                "description": "Echo back the input",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"}
                    },
                    "required": ["message"]
                },
                "callable": lambda message: message
            }
        }

    setup_module_with_tools("echo_ext", tools)
    ext_mgr = SimpleNamespace(extensions={"echo_ext": "echo_ext"})
    tools_out = list_ai_tools(ext_mgr)

    assert len(tools_out) == 1
    assert "echo" in tools_out[0]
    assert callable(tools_out[0]["echo"]["callable"])


def test_multiple_tools_in_one_extension():
    def tools():
        return {
            "add": {
                "description": "Add numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                },
                "callable": lambda a, b: a + b
            },
            "subtract": {
                "description": "Subtract numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                },
                "callable": lambda a, b: a - b
            }
        }

    setup_module_with_tools("math_ext", tools)
    ext_mgr = SimpleNamespace(extensions={"math_ext": "math_ext"})
    tools_out = list_ai_tools(ext_mgr)

    assert len(tools_out) == 1
    assert "add" in tools_out[0]
    assert "subtract" in tools_out[0]


def test_extension_missing_tools_function():
    sys.modules["no_tools_ext"] = SimpleNamespace()
    ext_mgr = SimpleNamespace(extensions={"no_tools_ext": "no_tools_ext"})
    tools_out = list_ai_tools(ext_mgr)

    assert tools_out == []


def test_tools_function_raises_exception():
    def tools():
        raise ValueError("Oops!")

    setup_module_with_tools("error_ext", tools)
    ext_mgr = SimpleNamespace(extensions={"error_ext": "error_ext"})

    # Capture printed error message
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        tools_out = list_ai_tools(ext_mgr)
        printed = buf.getvalue()

    assert tools_out == []
    assert "Oops!" in printed


def test_module_does_not_exist():
    ext_mgr = SimpleNamespace(extensions={"nonexistent": "nonexistent"})

    # Capture printed error message
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        tools_out = list_ai_tools(ext_mgr)
        printed = buf.getvalue()

    assert tools_out == []
    assert "No module named 'nonexistent'" in printed
