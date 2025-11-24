import datetime
import http.server
import http.client
import urllib.parse

from . import __version__
from . import utils
from .messages import NKRequest, NKResponse
from .router import NKRouter

class NKRequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = f"NKAPI/{__version__}"

    def __init__(self, router, debug, cors_origins, cors_headers, *args, **kwargs):
        self.router = router
        self.debug = debug
        self.cors_origins = cors_origins
        self.cors_headers = cors_headers
        super().__init__(*args, **kwargs)

    def _cors_origin(self):
        origin = self.headers.get("Origin")
        if not origin:
            return None
        if "*" in self.cors_origins:
            return "*"
        if origin in self.cors_origins:
            return origin
        return None
    
    def _apply_cors(self, response):
        origin = self._cors_origin()
        if not origin:
            return
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"

    def handle_request(self):
        request = NKRequest.from_handler(self)
        response = self.router.handle(request)
        self.respond(response)
    
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def do_PUT(self): self.handle_request()
    def do_DELETE(self): self.handle_request()
    def do_PATCH(self): self.handle_request()
    def do_HEAD(self): self.handle_request()
    def do_OPTIONS(self):
        origin = self._cors_origin()
        path = urllib.parse.urlsplit(self.path).path
        requested_method = self.headers.get("Access-Control-Request-Method")
        requested_headers = self.headers.get("Access-Control-Request-Headers")

        if origin == "*" or origin in self.cors_origins:
            allowed_methods = self.router.allowed_methods(path)
        else:
            allowed_methods = []

        allow_methods = ", ".join(sorted(set(allowed_methods + ["OPTIONS"])))
        allow_headers = requested_headers or ", ".join(self.cors_headers)

        response = NKResponse(
            status=200,
            headers={
                "Content-Type": "text/plain",
                "Access-Control-Allow-Origin": origin if origin else "",
                "Access-Control-Allow-Methods": allow_methods,
                "Access-Control-Allow-Headers": allow_headers,
                "Vary": "Origin"
            }
        )

        self.respond(response)

    def respond(self, response: NKResponse):
        self._apply_cors(response)
        self.send_response(response.status)
        body = response.body
        for header, value in response.headers.items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):        
        timestamp = datetime.datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
        
        method = getattr(self, "command", None) or "-"
        path = getattr(self, "path", None) or "-"
        version = getattr(self, "request_version", None) or "-"
        status = args[1] if len(args) > 1 else "-"

        a = utils.ANSI
        color = {
            "2": a.WHITE, "3": a.CYAN, "4": a.YELLOW, "5": a.MAGENTA
        }.get(str(status)[0], "")

        print(
            f"{self.client_address[0]} - - [{timestamp}] "
            f"\"{color}{method} {path} {version}{a.RESET}\" {status} -"
        )

class NKServer:
    def __init__(self, host="127.0.0.1", port=8000, debug=True, cors_origins=None, cors_headers=None):
        self.host = host
        self.port = port if port != 0 else utils.get_free_port(self.host)
        self.debug = bool(debug)

        self.cors_origins = cors_origins or ["*"]
        self.cors_headers = cors_headers or ["Content-Type", "Authorization"]

        self.router = NKRouter(debug=self.debug)
        self.handler = lambda *args, **kwargs: NKRequestHandler(
            self.router, self.debug, self.cors_origins, self.cors_headers, *args, **kwargs
        )

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
            
            return [response.body] if environ.get("REQUEST_METHOD", "GET") != "HEAD" else []
        return app

    def start(self):
        print(
            "* Serving NKAPI app",
            f"* Debug mode: {['off', 'on'][int(self.debug)]}",
            sep="\n"
        )

        if self.debug:
            print(f"{utils.ANSI.RED}* WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.{utils.ANSI.RESET}")

        print(
            f"* Running on http://{self.host}:{self.port}/",
            f"{utils.ANSI.YELLOW}* Press CTRL+C to quit{utils.ANSI.RESET}",
            sep="\n"
        )

        self.httpd = http.server.HTTPServer(
            (self.host, self.port),
            self.handler
        )

        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n* Closing the server...")
            self.httpd.server_close()
            exit(0)
