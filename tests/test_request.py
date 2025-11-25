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

def test_request_with_nonstandard_method_and_path_characters():
    request = nkapi.NKRequest(method="GE T", path="/weird path/💀🔥")
    assert request.method == "GE T"
    assert request.path == "/weird path/💀🔥"

def test_request_query_keys_with_empty_lists_and_nested_empty_lists():
    request = nkapi.NKRequest(method="GET", path="/", query={"a": [], "b": [[]], "c": ["val"]})
    assert request.query == {"a": [], "b": [[]], "c": "val"}

def test_request_with_headers_containing_non_ascii_and_mixed_case():
    request = nkapi.NKRequest(method="GET", path="/", headers={"X-Ünicode": "✓", "x-Mixed": "VaLue"})
    assert request.headers["X-Ünicode"] == "✓"
    assert request.headers["X-Mixed"] == "VaLue"

def test_request_with_body_as_integer_or_non_string_non_bytes_values():
    request = nkapi.NKRequest(method="POST", path="/", body=12345)
    assert request.body == 12345

def test_request_from_handler_reads_partial_body_if_content_length_smaller():
    class Dummy:
        def __init__(self):
            self.command = "POST"
            self.path = "/partial"
            self.headers = {"Content-Length": "4", "Content-Type": "text/plain"}
            self.rfile = io.BytesIO(b"abcdef")
            self.client_address = ("1.2.3.4", 80)

    request = nkapi.NKRequest.from_handler(Dummy())
    assert request.body == "abcd"

def test_request_from_handler_with_missing_rfile_does_not_crash():
    class Dummy:
        def __init__(self):
            self.command = "GET"
            self.path = "/"
            self.headers = {}
            self.client_address = ("0.0.0.0", 0)
            self.rfile = None

    request = nkapi.NKRequest.from_handler(Dummy())
    assert request.body is None

def test_request_from_environ_with_missing_wsgi_input_returns_none():
    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/"}
    request = nkapi.NKRequest.from_environ(environ)
    assert request.body is None

def test_request_body_with_invalid_utf8_bytes_does_not_crash():
    body = b"\xff\xfe\xfd"
    request = nkapi.NKRequest(method="POST", path="/", body=body, headers={"Content-Type": "application/json"})
    assert request.body == body

def test_request_query_with_encoded_unicode_and_percent_signs():
    request = nkapi.NKRequest(method="GET", path="/", query={"q": ["%F0%9F%98%81", "%25"]})
    assert request.query == {"q": ["%F0%9F%98%81", "%25"]}

def test_request_with_multiple_content_type_headers_prioritizes_last():
    request = nkapi.NKRequest(method="GET", path="/", headers={"Content-Type": "text/plain", "CONTENT-TYPE": "application/json"}, body='{"x":1}')
    assert isinstance(request.body, dict)
    assert request.body == {"x": 1}

def test_request_from_environ_with_non_integer_content_length_reads_none():
    environ = {"REQUEST_METHOD": "POST", "PATH_INFO": "/", "CONTENT_LENGTH": "abc", "wsgi.input": io.BytesIO(b"xyz")}
    request = nkapi.NKRequest.from_environ(environ)
    assert request.body is None

def test_request_from_environ_with_missing_content_type_assumes_bytes():
    body = "hello"
    environ = {"REQUEST_METHOD": "POST", "PATH_INFO": "/", "CONTENT_LENGTH": str(len(body)), "wsgi.input": io.BytesIO(body.encode())}
    request = nkapi.NKRequest.from_environ(environ)
    assert request.body == body

def test_request_with_large_binary_body_and_json_content_type_safe_handling():
    giant = b"x" * 5_000_000
    request = nkapi.NKRequest(method="POST", path="/big", headers={"Content-Type": "application/json"}, body=giant)
    assert request.body == giant

def test_request_with_headers_containing_non_string_values_converted_to_string():
    request = nkapi.NKRequest(method="GET", path="/", headers={"X-Number": 123, "X-None": None})
    assert request.headers["X-Number"] == "123"
    assert request.headers["X-None"] == "None"

def test_request_with_body_as_list_or_dict_returns_as_is():
    body = {"a": 1}
    request = nkapi.NKRequest(method="POST", path="/", body=body)
    assert request.body == body
    body_list = [1, 2, 3]
    request_list = nkapi.NKRequest(method="POST", path="/", body=body_list)
    assert request_list.body == body_list

def test_request_with_multiple_query_values_same_key_preserves_list_when_needed():
    request = nkapi.NKRequest(method="GET", path="/", query={"x": ["1", "2"], "y": ["single"]})
    assert request.query == {"x": ["1", "2"], "y": "single"}
