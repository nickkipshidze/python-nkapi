import json
import urllib.parse

class NKRequest:
    def __init__(self, method, path, query=None, headers=None, body=None, client_address=None):
        self.method = method
        self.path = path
        query = query or {}
        self.query = {k: v[0] if len(v) == 1 else v for k, v in query.items()}
        self.params = {}
        self.headers = headers or {}
        self.body = body
        self.client_address = client_address

        if "application/json" in self.headers.get("Content-Type", "").lower() and isinstance(self.body, str):
            try:
                self.body = json.loads(self.body)
            except json.decoder.JSONDecodeError:
                print("* Warning: Couldn't decode json in the request body.")
                
    @classmethod
    def from_handler(cls, handler):
        length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(length).decode("utf-8") if length > 0 else None
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
        body = environ["wsgi.input"].read(length).decode("utf-8") if length > 0 else None

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
