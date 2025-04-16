from jupyter_server.extension.application import ExtensionApp
from jupyter_server.utils import url_path_join
from .handlers import ListExtensionsHandler, ListToolInfoHandler


class Extension(ExtensionApp):
    # Required traits
    name = "list_ai_tools"
    default_url = "/list_ai_tools"
    load_other_extensions = True  # Allow loading other extensions (important for introspection)

    def initialize_handlers(self):
        """Register API route handlers."""
        base_url = self.serverapp.web_app.settings["base_url"]
        route_pattern_1 = url_path_join(base_url, self.default_url, "extensions")
        route_pattern_2 = url_path_join(base_url, self.default_url, "tools")

        self.handlers.extend([
            (route_pattern_1, ListExtensionsHandler),
            (route_pattern_2, ListToolInfoHandler),
        ])
