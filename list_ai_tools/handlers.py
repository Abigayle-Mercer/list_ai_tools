import json
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from .list_ai_tools import list_ai_tools
import tornado
import importlib



class ListExtensionsHandler(APIHandler):
    @tornado.web.authenticated
    async def get(self):
        extension_names = list(self.serverapp.extension_manager.extensions.keys())
        self.finish(json.dumps({"extensions": extension_names}))
        return



class ListToolInfoHandler(APIHandler):
    @tornado.web.authenticated
    async def get(self):
        raw_tools = list_ai_tools(self.serverapp.extension_manager)
        safe_tools = {}

        for ext in raw_tools:
            if isinstance(ext, dict):
                for tool_name, tool_info in ext.items():
                    if isinstance(tool_info, dict):
                        filtered_info = {
                            k: v for k, v in tool_info.items() if k != "callable"
                        }
                        if tool_name not in safe_tools:
                            safe_tools[tool_name] = filtered_info
            elif isinstance(ext, list):
                # Optional: handle if `tools()` returns a list
                continue

        self.finish(json.dumps({"discovered_tools": safe_tools}))

