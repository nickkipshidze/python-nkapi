import traceback

from .request import NKRequest
from .response import NKResponse

class NKRouter:
    def __init__(self):
        self.routes = {}
    
    def register(self, methods, path, callback):
        for method in methods:
            self.routes[(method.upper(), path)] = callback
    
    def handle(self, request: NKRequest):
        handler = self.routes.get((request.method.upper(), request.path))

        if handler != None:
            try:
                return handler(request)
            except Exception as error:
                traceback.print_exception(error)
                return NKResponse(data="500 Internal Server Error", status=500)
            
        return NKResponse(data="404 Not Found", status=404)
