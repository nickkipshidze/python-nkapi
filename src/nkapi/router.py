import traceback

from .messages import NKRequest, NKResponse

class RouteNode:
    def __init__(self):
        self.children = {}
        self.handler = None
        self.param_name = None

class NKRouter:
    def __init__(self, debug=False):
        self.routes = {}
        self.debug = debug
    
    def register(self, methods, path, view):
        parts = path.strip("/").split("/")
        for method in methods:
            method = method.upper()
            if method not in self.routes:
                self.routes[method] = RouteNode()
            node: RouteNode = self.routes[method]

            for part in parts:
                if part.startswith("<") and part.endswith(">"):
                    key = "<param>"
                    param_name = part[1:-1]
                    if key not in node.children:
                        node.children[key] = RouteNode()
                    node = node.children[key]
                    node.param_name = param_name
                else:
                    if part not in node.children:
                        node.children[part] = RouteNode()
                    node = node.children[part]

            node.handler = view

    def allowed_methods(self, path):
        path_parts = path.strip("/").split("/")
        allowed = []
        for method, root in self.routes.items():
            handler, _ = self._match(root, path_parts, {})
            if handler:
                allowed.append(method)
        return allowed

    def _match(self, node: RouteNode, parts, params):
        if not parts:
            return (node.handler, params) if node.handler else (None, {})
        
        part = parts[0]
        if part in node.children:
            handler, p = self._match(node.children[part], parts[1:], params.copy())
            if handler:
                return handler, p
            
        if "<param>" in node.children:
            child = node.children["<param>"]
            new_params = params.copy()
            new_params[child.param_name] = part
            handler, p = self._match(child, parts[1:], new_params)
            if handler:
                return handler, p
            
        return None, {}

    def handle(self, request: NKRequest):
        method = request.method.upper()
        path_parts = request.path.strip("/").split("/")

        if method in self.routes:
            handler, params = self._match(self.routes[method], path_parts, {})
            if handler:
                request.params = params
                try:
                    return handler(request)
                except Exception as error:
                    if self.debug:
                        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                        return NKResponse(body=tb, status=500)
                    else:
                        traceback.print_exception(error)
                        return NKResponse(body="500 Internal Server Error", status=500)
            
        allowed = self.allowed_methods(request.path)
        if allowed:
            return NKResponse(
                headers={"Allow": ", ".join(allowed)},
                body="405 Method Not Allowed",
                status=405
            )
            
        return NKResponse(body="404 Not Found", status=404)
