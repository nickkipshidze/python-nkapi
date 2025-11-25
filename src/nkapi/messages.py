import json
import urllib.parse

class NKHeaders(dict):
    def __init__(self, map=None, **kwargs):
        super().__init__()
        map = map or {}
        for key, value in map.items():
            self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def __setitem__(self, key, value):
        key = key.title()

        if isinstance(value, str):
            value = int(value) if value.isdigit() else value

        if key in self and isinstance(value, str):
            value = self[key] + "; " + str(value)
        
        super().__setitem__(key, str(value))
        
    def __getitem__(self, key):
        value = super().__getitem__(key.title())
        return value

class NKResponse:
    def __init__(self, headers=None, body=None, status=200):
        self.headers = NKHeaders(headers or {})
        self._body = body or ""
        self.status = status

        if "Content-Type" not in self.headers:
            if isinstance(self._body, (dict, list, tuple)):
                self.headers["Content-Type"] = "application/json"
            elif not isinstance(self._body, bytes):
                self.headers["Content-Type"] = "text/plain; charset=utf-8"
            else:
                self.headers["Content-Type"] = "application/octet-stream"
        
        self.body

    @property
    def body(self):
        body = self._body

        if "application/json" in self.headers.get("Content-Type", "").lower():
            if isinstance(body, (dict, list, tuple)):
                body = json.dumps(body, indent=4)

        if not isinstance(body, bytes):
            body = str(body).encode("utf-8", errors="ignore")

        self.headers["Content-Length"] = len(body)

        return body
    
    @body.setter
    def body(self, value):
        self._body = value

    def __str__(self):
        return f"<nkapi.NKResponse - \"{self.body[:16]}\" {self.status}>"
    
    def __repr__(self):
        return self.__str__()

class NKRequest:
    def __init__(self, method, path, query=None, headers=None, body=None, client_address=None):
        self.method = method
        self.path = path
        query = query or {}
        self.query = {k: v[0] if len(v) == 1 else v for k, v in query.items()}
        self.params = {}
        self.headers = NKHeaders(headers or {})
        self.body = body
        self.client_address = client_address

        if "application/json" in self.headers.get("Content-Type", "").lower() and isinstance(self.body, str):
            try:
                self.body = json.loads(self.body)
            except json.decoder.JSONDecodeError:
                print("* Warning: Couldn't decode json in the request body.")
                
    @classmethod
    def from_handler(cls, handler):
        try:
            length = int(handler.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            length = 0
            
        body = handler.rfile.read(length).decode("utf-8", errors="ignore") if length > 0 else None
        parsed = urllib.parse.urlparse(handler.path)
        
        return cls(
            method=handler.command,
            path=parsed.path,
            query=urllib.parse.parse_qs(parsed.query),
            headers=dict(handler.headers),
            body=body,
            client_address=handler.client_address
        )

    @classmethod
    def from_environ(cls, environ):
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

        body = environ["wsgi.input"].read(length).decode("utf-8", errors="ignore") if length > 0 else None

        return cls(
            method=environ.get("REQUEST_METHOD", "GET"),
            path=environ.get("PATH_INFO", "/"),
            query=urllib.parse.parse_qs(environ.get("QUERY_STRING", "")),
            headers=headers,
            body=body,
            client_address=(environ.get("REMOTE_ADDR", ""), environ.get("REMOTE_PORT", 0))
        )

    def __str__(self):
        return f"<nkapi.NKRequest - \"{self.method} {self.path}\">"

    def __repr__(self):
        return self.__str__()
