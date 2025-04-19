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
        metadata_only = True  # Optionally make this dynamic from query param later
        raw_tools = list_ai_tools(self.serverapp.extension_manager, return_metadata_only=metadata_only)

        # If metadata_only=True, raw_tools is already safe
        self.finish(json.dumps({"discovered_tools": raw_tools}))


