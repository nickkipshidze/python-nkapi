import io
import json
import nkapi

def test_request_basic_initialization_and_query_flattening():
    request = nkapi.NKRequest(
        method="GET",
        path="/alpha",
        query={"x": ["1"], "y": ["a", "b"]},
        headers={"Content-Type": "text/plain"},
        body=None,
        client_address=("127.0.0.1", 1234)
    )
    assert request.method == "GET"
    assert request.path == "/alpha"
    assert request.query == {"x": "1", "y": ["a", "b"]}
    assert request.params == {}
    assert request.headers["Content-Type"] == "text/plain"
    assert request.body is None
    assert request.client_address == ("127.0.0.1", 1234)
    
def test_request_json_auto_decode_valid():
    data = {"hello": "world"}
    body = json.dumps(data)
    request = nkapi.NKRequest(
        method="POST",
        path="/json",
        query={},
        headers={"Content-Type": "application/json"},
        body=body
    )
    assert request.body == data
    
def test_request_json_auto_decode_invalid_prints_warning(capfd):
    request = nkapi.NKRequest(
        method="POST",
        path="/json",
        headers={"Content-Type": "application/json"},
        body="{not valid json]"
    )
    captured = capfd.readouterr()
    assert "Warning" in captured.out
    assert isinstance(request.body, str)
    
def test_request_from_handler_parses_path_query_and_body():
    class DummyHandler:
        def __init__(self):
            self.command = "POST"
            self.path = "/abc?x=1&y=2"
            self.headers = {
                "Content-Type": "application/json",
                "Content-Length": "13"
            }
            self.client_address = ("10.0.0.1", 5555)
            self.rfile = io.BytesIO(b'{"a": 10}')

    handler = DummyHandler()
    request = nkapi.NKRequest.from_handler(handler)

    assert request.method == "POST"
    assert request.path == "/abc"
    assert request.query == {"x": "1", "y": "2"}
    assert request.body == {"a": 10}
    assert request.client_address == ("10.0.0.1", 5555)
    
def test_request_from_environ_parses_wsgi_environment():
    environ = {
        "REQUEST_METHOD": "PUT",
        "PATH_INFO": "/upload",
        "QUERY_STRING": "k=9&k=10",
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": "11",
        "REMOTE_ADDR": "78.105.99.107",
        "REMOTE_PORT": "443",
        "HTTP_X_TEST_HEADER": "xyz",
        "wsgi.input": io.BytesIO(b'{"x": 1}')
    }

    request = nkapi.NKRequest.from_environ(environ)

    assert request.method == "PUT"
    assert request.path == "/upload"
    assert request.query == {"k": ["9", "10"]}
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["X-Test-Header"] == "xyz"
    assert request.body == {"x": 1}
    assert request.client_address == ("78.105.99.107", "443")
    
def test_request_str_and_repr_are_consistent():
    request = nkapi.NKRequest("GET", "/xyz")
    assert str(request) == '<nkapi.NKRequest - "GET /xyz">'
    assert repr(request) == str(request)

def test_request_with_empty_method_and_empty_path():
    request = nkapi.NKRequest(method="", path="", query={}, headers={}, body=None)
    assert request.method == ""
    assert request.path == ""
    assert request.query == {}
    assert request.body is None
    
def test_request_with_unusual_unicode_path_and_query_keys():
    request = nkapi.NKRequest(
        method="GET",
        path="/💀🔥",
        query={"ключ": ["знач"], "🔥": ["x"]},
    )
    assert request.path == "/💀🔥"
    assert request.query == {"ключ": "знач", "🔥": "x"}
    
def test_request_with_header_case_insensitivity_and_multiple_types():
    request = nkapi.NKRequest(
        method="POST",
        path="/h",
        headers={"CONTENT-TYPE": "application/json", "Content-Type": "ignored"},
        body='{"a":1}',
    )
    assert isinstance(request.body, dict)
    assert request.body == {"a": 1}
    
def test_request_json_decode_with_bytes_body_and_wrong_header():
    request = nkapi.NKRequest(
        method="POST",
        path="/x",
        headers={"Content-Type": "application/json"},
        body=b'{"a":1}'
    )
    assert isinstance(request.body, bytes)
    
def test_request_from_handler_with_negative_or_invalid_length():
    class Dummy:
        def __init__(self, length):
            self.command = "POST"
            self.path = "/neg"
            self.headers = {"Content-Type": "application/json", "Content-Length": length}
            self.client_address = ("0.0.0.0", 1)
            self.rfile = io.BytesIO(b"")

    for bad_length in ["-10", "abc", None]:
        handler = Dummy(bad_length)
        request = nkapi.NKRequest.from_handler(handler)
        assert request.body is None
        
def test_request_from_environ_with_invalid_content_length():
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "CONTENT_LENGTH": "not-a-number",
        "wsgi.input": io.BytesIO(b"should not read"),
    }
    request = nkapi.NKRequest.from_environ(environ)
    assert request.body is None
    
def test_request_from_environ_with_binary_body_and_json_header():
    body = b'{"a": 5}'
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/",
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    request = nkapi.NKRequest.from_environ(environ)
    assert request.body == {"a": 5}
    
def test_request_query_with_empty_string_values_and_none():
    request = nkapi.NKRequest(
        method="GET",
        path="/",
        query={"a": [""], "b": ["", ""]},
    )
    assert request.query == {"a": "", "b": ["", ""]}
    
def test_request_with_enormous_body_does_not_crash(monkeypatch):
    giant = "x" * 5000000
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/big",
        "CONTENT_TYPE": "text/plain",
        "CONTENT_LENGTH": str(len(giant)),
        "wsgi.input": io.BytesIO(giant.encode("utf-8")),
    }
    request = nkapi.NKRequest.from_environ(environ)
    assert isinstance(request.body, str)
    assert len(request.body) == 5000000
    
def test_request_str_and_repr_survive_weird_values():
    request = nkapi.NKRequest(method=None, path=None)
    assert "None" in str(request)
    assert str(request) == repr(request)
