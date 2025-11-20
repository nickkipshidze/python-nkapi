import datetime
import http.server
import http.client

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
        request = NKRequest.from_handler(self)
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

        if self.command != "HEAD":
            self.wfile.write(response.body)
    
    def log_message(self, format, *args):
        timestamp = datetime.datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
        
        method = getattr(self, "command", None)
        path = getattr(self, "path", None)
        version = getattr(self, "request_version", None)
        status = args[1] if len(args) > 1 else "-"

        print(
            f"{self.client_address[0]} - - [{timestamp}] "
            f"\"{method} {path} {version}\" {status} -"
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

            if isinstance(response.body, str):
                response.body = response.body.encode("utf-8")
                
            return [response.body]
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
