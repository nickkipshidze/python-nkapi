import json

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
    def __init__(self, headers=None, body="", status=200):
        self.headers = NKHeaders(headers or {})
        self._body = body
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
            body = body.encode("utf-8", errors="ignore")

        self.headers["Content-Length"] = len(body)

        return body
    
    @body.setter
    def body(self, value):
        self._body = value

    def __str__(self):
        return f"<nkapi.NKResponse - \"{self.body[:16]}\" {self.status}>"
    
    def __repr__(self):
        return self.__str__()
