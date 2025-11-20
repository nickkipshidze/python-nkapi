import json

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
