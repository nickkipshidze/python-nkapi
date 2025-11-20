import json

class NKResponse:
    def __init__(self, headers=None, body="", status=200):
        self.headers = headers or {}
        self.body = body
        self.status = status

        if "application/json" in self.headers.get("Content-Type", "").lower() and isinstance(self.body, (dict, list, tuple)):
            self.body = json.dumps(self.body, indent=4)

        if not isinstance(self.body, bytes):
            if not "Content-Type" in self.headers:
                self.headers["Content-Type"] = "text/plain; charset=utf-8"
            self.body = self.body.encode("utf-8")
        
        self.headers["Content-Length"] = str(len(self.body))
