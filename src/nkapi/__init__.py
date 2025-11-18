import os
import sys
import json
import datetime
import http.server
import urllib.parse

__version__ = "25.11.18a"

class NKResponse:
    def __init__(self, headers={}, data="", status=200):
        self.headers = headers
        self.data = data
        self.status = status

        if "Content-Type" in headers and headers["Content-Type"] == "application/json" and type(data) == dict:
            self.data = json.dumps(self.data)

        self.headers["Content-Length"] = len(self.data.encode("utf-8"))

class NKRequest:
    def __init__(self, handler: http.server.BaseHTTPRequestHandler, body=None):
        self.method = handler.command
        self.raw_path = handler.path
        
        parsed = urllib.parse.urlparse(handler.path)
        self.path = parsed.path
        self.query = urllib.parse.parse_qs(parsed.query)

        self.headers = dict(handler.headers)
        self.body = body
        self.client_address = handler.client_address
        self.handler = handler

    def __str__(self):
        return f"<nkapi.NKRequest - \"{self.method} {self.path}\">"

    def __repr__(self):
        return self.__str__()

class NKRequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = f"NKAPI/{__version__}"

    def __init__(self, router, *args, **kwargs):
        self.router = router
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        request = NKRequest(handler=self, body=None)
        response = self.router.handle(request)
        self.respond(response)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        request = NKRequest(handler=self, body=body)
        response = self.router.handle(request)
        self.respond(response)
    
    def respond(self, response: NKResponse):
        self.send_response(response.status)
        
        for header, value in response.headers.items():
            self.send_header(header, value)
        self.end_headers()

        self.wfile.write(response.data.encode("utf-8"))
    
    def log_message(self, format, *args):
        timestamp = datetime.datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
        print(f"{self.client_address[0]} - - [{timestamp}] \"{self.command} {self.path} {self.request_version}\" {args[1]} -")
    
class NKRouter:
    def __init__(self):
        self.routes = {}
    
    def register(self, method, path, callback):
        self.routes[(method, path)] = callback
    
    def handle(self, request: NKRequest):
        handler = self.routes.get((request.method, request.path))
        if handler:
            return handler(request)
        return NKResponse(status=404)

class NKServer:
    def __init__(self, host="localhost", port=8000, debug=True):
        self.host = host
        self.port = port
        self.debug = bool(debug)

        self.router = NKRouter()
        self.handler = self.make_handler(self.router)

        self.httpd = http.server.HTTPServer(
            (self.host, self.port),
            self.handler
        )

    def make_handler(self, router):
        def handler(*args, **kwargs):
            NKRequestHandler(router, *args, **kwargs)
        return handler

    def start(self):
        print(
            "* Serving NKAPI app",
            f"* Debug mode: {self.debug}",
            f"* Running on http://{self.host}:{self.port}/",
            sep="\n"
        )

        self.httpd.serve_forever()
