import json
import datetime
import traceback
import http.server
import urllib.parse

__version__ = "0.1.1"

class NKResponse:
    def __init__(self, headers=None, data="", status=200):
        self.headers = headers or {}
        self.data = data
        self.status = status

        if self.headers.get("Content-Type") == "application/json" and isinstance(self.data, dict):
            self.data = json.dumps(self.data)

        if isinstance(self.data, str):
            self.data = self.data.encode("utf-8")
        
        self.headers["Content-Length"] = len(self.data)

class NKRequest:
    def __init__(self, method, path, query=None, headers=None, body=None, client_address=None):
        self.method = method
        self.path = path
        self.query = query or {}
        self.headers = headers or {}
        self.body = body
        self.client_address = client_address
        self.raw_path = path

        if self.headers.get("Content-Type") == "application/json" and isinstance(self.body, str):
            try:
                self.body = json.loads(self.body)
            except json.decoder.JSONDecodeError:
                print("* Warning: Couldn't decode json in the request body.")

    @classmethod
    def from_environ(cls, environ):
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "/")
        query = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))

        headers = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").title()
                headers[header_name] = value
            elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                header_name = key.replace("_", "-").title()
                headers[header_name] = value

        try:
            length = int(environ.get("CONTENT_LENGTH", 0))
        except (ValueError, TypeError):
            length = 0
        body = environ["wsgi.input"].read(length).decode("utf-8") if length > 0 else None

        client_address = (environ.get("REMOTE_ADDR", ""), environ.get("REMOTE_PORT", 0))
        return cls(method, path, query, headers, body, client_address)

    def __str__(self):
        return f"<nkapi.NKRequest - \"{self.method} {self.path}\">"

    def __repr__(self):
        return self.__str__()

class NKRequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = f"NKAPI/{__version__}"

    def __init__(self, router, *args, **kwargs):
        self.router = router
        super().__init__(*args, **kwargs)

    def handle_request(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else None

        parsed = urllib.parse.urlparse(self.path)

        request = NKRequest(
            method=self.command,
            path=parsed.path,
            query=urllib.parse.parse_qs(parsed.query),
            headers=dict(self.headers),
            body=body
        )

        response = self.router.handle(request)
        self.respond(response)
    
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def do_PUT(self): self.handle_request()
    def do_DELETE(self): self.handle_request()
    def do_PATCH(self): self.handle_request()
    def do_OPTIONS(self): self.handle_request()
    def do_HEAD(self): self.handle_request()

    def respond(self, response: NKResponse):
        self.send_response(response.status)
        
        for header, value in response.headers.items():
            self.send_header(header, value)
        self.end_headers()

        self.wfile.write(response.data)
    
    def log_message(self, format, *args):
        timestamp = datetime.datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
        print(f"{self.client_address[0]} - - [{timestamp}] \"{self.command} {self.path} {self.request_version}\" {args[1]} -")
    
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

class NKServer:
    def __init__(self, host="127.0.0.1", port=8000, debug=True):
        self.host = host
        self.port = port
        self.debug = bool(debug)

        self.router = NKRouter()
        self.handler = lambda *args, **kwargs: NKRequestHandler(self.router, *args, **kwargs)

    @property
    def wsgi_app(self):
        def app(environ, start_response):
            request = NKRequest.from_environ(environ)
            response = self.router.handle(request)

            status_line = f"{response.status} {http.client.responses.get(response.status, "")}"
            headers = [(k, str(v)) for k, v in response.headers.items()]
            start_response(status_line, headers)
            return [response.data.encode("utf-8")]
        return app

    def start(self):
        print(
            "* Serving NKAPI app",
            f"* Debug mode: {self.debug}",
            f"* Running on http://{self.host}:{self.port}/",
            sep="\n"
        )

        self.httpd = http.server.HTTPServer(
            (self.host, self.port),
            self.handler
        )

        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("* Closing the server...")
            self.httpd.server_close()
            exit(0)
