import datetime
import http.server
import urllib.parse

from . import __version__
from .request import NKRequest
from .response import NKResponse
from .router import NKRouter

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
        
        method = getattr(self, "command", None)
        path = getattr(self, "path", None)
        version = getattr(self, "request_version", None)

        print(
            f"{self.client_address[0]} - - [{timestamp}] "
            f"\"{method} {path} {version}\" {args[1]} -"
        )

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

            if isinstance(response.data, str):
                response.data = response.data.encode("utf-8")
                
            return [response.data]
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
