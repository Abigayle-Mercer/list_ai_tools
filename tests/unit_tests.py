import sys
import json
import pytest
from types import SimpleNamespace
from list_ai_tools.list_ai_tools import (
    list_ai_tools,
    run,
    CALLABLE_REGISTRY,
    parse_standard_tool_call,
    parse_openai_tool_call,
)

# --- Test Setup ---

def setup_module_with_tools(name, tools_func):
    sys.modules[name] = SimpleNamespace(jupyter_server_extension_tools=tools_func)

# --- Tests for list_ai_tools ---

def test_valid_extension_single_tool():
    def greet(name="World"):
        return f"Hello, {name}!"

    def tools():
        return {
            "say_hello": {
                "metadata": {
                    "say_hello": {
                        "description": "Greets someone",
                        "parameters": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            "required": []
                        }
                    }
                },
                "callable": greet
            }
        }

    setup_module_with_tools("mock_ext", tools)
    ext_mgr = SimpleNamespace(extensions={"mock_ext": "mock_ext"})
    tools_out = list_ai_tools(ext_mgr)

    assert isinstance(tools_out[0]["say_hello"], dict)
    assert CALLABLE_REGISTRY["say_hello"]("Test") == "Hello, Test!"

def test_duplicate_tool_name_raises_error_message():
    def tools_a():
        return {
            "dup": {
                "metadata": {
                    "dup": {
                        "description": "First",
                        "parameters": {"type": "object", "properties": {}, "required": []}
                    }
                },
                "callable": lambda: "A"
            }
        }

    def tools_b():
        return {
            "dup": {
                "metadata": {
                    "dup": {
                        "description": "Second",
                        "parameters": {"type": "object", "properties": {}, "required": []}
                    }
                },
                "callable": lambda: "B"
            }
        }

    sys.modules["a"] = SimpleNamespace(jupyter_server_extension_tools=tools_a)
    sys.modules["b"] = SimpleNamespace(jupyter_server_extension_tools=tools_b)

    ext_mgr = SimpleNamespace(extensions={"a": "a", "b": "b"})
    result = list_ai_tools(ext_mgr)

    assert any("Duplicate tool name detected" in r.get("error", "") for r in result)

def test_invalid_tool_schema_triggers_error():
    def tools():
        return {
            "broken": {
                "metadata": {
                    "broken": {
                        "description": "This one forgot parameters"
                    }
                },
                "callable": lambda: "oops"
            }
        }

    setup_module_with_tools("bad_ext", tools)
    ext_mgr = SimpleNamespace(extensions={"bad_ext": "bad_ext"})
    tools_out = list_ai_tools(ext_mgr)

    assert tools_out[0]["error"].startswith("Schema validation failed")

def test_valid_custom_anthropic_schema():
    anthropic_schema = {
        "type": "object",
        "patternProperties": {
            "^[a-zA-Z_][a-zA-Z0-9_]*$": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "parameters": {"type": "object"}
                },
                "required": ["description", "parameters"]
            }
        }
    }

    def tools():
        return {
            "some_tool": {
                "metadata": {
                    "some_tool": {
                        "description": "Test for Anthropic-like metadata",
                        "parameters": {}
                    }
                },
                "callable": lambda: "ok"
            }
        }

    setup_module_with_tools("anthropic_ext", tools)
    ext_mgr = SimpleNamespace(extensions={"anthropic_ext": "anthropic_ext"})
    tools_out = list_ai_tools(ext_mgr, schema=anthropic_schema)

    assert isinstance(tools_out[0]["some_tool"], dict)

# --- Tests for run() ---

def test_run_with_standard_call_executes_tool():
    def tools():
        def multiply(a, b): return a * b
        return {
            "multiply": {
                "metadata": {
                    "multiply": {
                        "description": "Multiplies two numbers",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "a": {"type": "number"},
                                "b": {"type": "number"}
                            },
                            "required": ["a", "b"]
                        }
                    }
                },
                "callable": multiply
            }
        }

    setup_module_with_tools("math_ext", tools)
    list_ai_tools(SimpleNamespace(extensions={"math_ext": "math_ext"}))

    calls = [{"name": "multiply", "arguments": {"a": 3, "b": 2}}]
    result = run(calls)
    assert result == [6]

def test_run_with_openai_style_call():
    def tools():
        def reverse(text): return text[::-1]
        return {
            "reverse": {
                "metadata": {
                    "reverse": {
                        "description": "Reverses text",
                        "parameters": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}},
                            "required": ["text"]
                        }
                    }
                },
                "callable": reverse
            }
        }

    setup_module_with_tools("str_ext", tools)
    list_ai_tools(SimpleNamespace(extensions={"str_ext": "str_ext"}))

    calls = [{
        "type": "function",
        "function": {
            "name": "reverse",
            "arguments": json.dumps({"text": "OpenAI"})
        }
    }]
    result = run(calls, parse_fn=parse_openai_tool_call)
    assert result == ["IAnepO"]
