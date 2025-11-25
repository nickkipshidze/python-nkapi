import io
import time
import json
import nkapi
import requests
import threading
import http.server
from wsgiref.validate import validator
from wsgiref.util import setup_testing_defaults

def start_test_server(server):
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.2)
    return thread

def test_real_http_server_end_to_end():
    server = nkapi.NKServer(host="127.0.0.1", port=0)
    server.router.register(["GET"], "/hello",
        lambda req: nkapi.NKResponse(body="world")
    )

    httpd = server.httpd = server.httpd = server.httpd = None
    def real_start():
        httpd_local = server.httpd = http.server.HTTPServer(("127.0.0.1", 0), server.handler)
        server.port = httpd_local.server_port
        httpd_local.serve_forever()

    thread = threading.Thread(target=real_start, daemon=True)
    thread.start()
    time.sleep(0.1)

    url = f"http://127.0.0.1:{server.port}/hello"
    response = requests.get(url)

    assert response.status_code == 200
    assert response.text == "world"

    server.httpd.shutdown()

def run_wsgi_app(app, method="GET", path="/", query="", body=b"", headers=None):
    environ = {}
    setup_testing_defaults(environ)
    environ["REQUEST_METHOD"] = method
    environ["PATH_INFO"] = path
    environ["QUERY_STRING"] = query
    environ["CONTENT_LENGTH"] = str(len(body))
    environ["wsgi.input"] = io.BytesIO(body)

    if headers:
        for key, value in headers.items():
            environ["HTTP_" + key.upper().replace("-", "_")] = value

    captured = {}
    def start_response(status, response_headers):
        captured["status"] = status
        captured["headers"] = response_headers

    result = b"".join(app(environ, start_response))
    return captured["status"], dict(captured["headers"]), result
    
def test_wsgi_basic_json_route():
    server = nkapi.NKServer()
    server.router.register(
        ["GET"], "/x",
        lambda request: nkapi.NKResponse(
            headers={"Content-Type": "application/json"},
            body={"a": 1}
        )
    )

    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/x")
    assert status.startswith("200")
    assert headers["Content-Type"] == "application/json"
    assert body == b"{\n    \"a\": 1\n}"
    
def test_wsgi_missing_content_length():
    server = nkapi.NKServer()
    server.router.register(["POST"], "/", lambda r: nkapi.NKResponse(body="ok"))

    status, headers, body = run_wsgi_app(server.wsgi_app, method="POST", body=b"data")
    assert body == b"ok"

def test_wsgi_json_body_sent_as_string_is_encoded_once():
    server = nkapi.NKServer()
    server.router.register(["POST"], "/",
        lambda request: nkapi.NKResponse(headers={"Content-Type": "application/json"}, body=request.body)
    )

    raw = b'{"x":10}'
    status, headers, body = run_wsgi_app(
        server.wsgi_app,
        method="POST",
        path="/",
        body=raw,
        headers={"Content-Type": "application/json"}
    )

    assert status.startswith("200")
    assert json.loads(body.decode("utf-8")) == {"x": 10}
    
def test_wsgi_multiple_query_params_and_decoding():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/q",
        lambda request: nkapi.NKResponse(body=str(request.query))
    )

    status, _, body = run_wsgi_app(server.wsgi_app, "GET", "/q", query="a=1&a=2&b=%F0%9F%94%A5")
    decoded = body.decode("utf-8")
    assert "['1', '2']" in decoded
    assert "🔥" in decoded
    
def test_wsgi_headers_case_insensitivity_and_passthrough():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/h",
        lambda request: nkapi.NKResponse(headers={"X-Test": request.headers.get("X-Test")}, body="ok")
    )

    status, headers, body = run_wsgi_app(
        server.wsgi_app, "GET", "/h",
        headers={"x-test": "Value123"}
    )

    assert headers["X-Test"] == "Value123"
    assert body == b"ok"
    
def test_wsgi_non_utf8_body_does_not_crash():
    server = nkapi.NKServer()
    server.router.register(["POST"], "/binary",
        lambda request: nkapi.NKResponse(body="done")
    )

    status, headers, body = run_wsgi_app(
        server.wsgi_app,
        method="POST",
        path="/binary",
        body=b"\xff\xfe\xfd"
    )

    assert body == b"done"
    
def test_wsgi_large_body_handling():
    server = nkapi.NKServer()
    server.router.register(["POST"], "/big",
        lambda request: nkapi.NKResponse(body=str(len(request.body or b'')))
    )

    blob = b"x" * 2_000_000
    status, headers, body = run_wsgi_app(
        server.wsgi_app,
        method="POST",
        path="/big",
        body=blob,
        headers={"Content-Type": "application/octet-stream"}
    )

    assert body == b"2000000"
    
def test_wsgi_head_request_suppresses_body():
    server = nkapi.NKServer()
    server.router.register(["HEAD"], "/head",
        lambda request: nkapi.NKResponse(body="should-not-return")
    )

    status, headers, body = run_wsgi_app(server.wsgi_app, "HEAD", "/head")
    assert status.startswith("200")
    assert body == b""
    
def test_wsgi_route_not_found_returns_404():
    server = nkapi.NKServer()
    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/nope")
    assert status.startswith("404")
    assert b"" == body or b"404" in body
    
def test_wsgi_malformed_query_string():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/fail",
        lambda request: nkapi.NKResponse(body=str(request.query))
    )

    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/fail", query="=1&?x&&y=2")
    text = body.decode("utf-8")
    assert isinstance(text, str)

def test_wsgi_method_not_allowed_returns_405():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/onlyget", lambda r: nkapi.NKResponse(body="ok"))

    status, headers, body = run_wsgi_app(server.wsgi_app, "POST", "/onlyget")
    assert status.startswith("405")
    assert b"" == body or b"405" in body

def test_wsgi_redirect_response():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/old", lambda r: nkapi.NKResponse(status=302, headers={"Location": "/new"}))

    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/old")
    assert status.startswith("302")
    assert headers["Location"] == "/new"

def test_wsgi_custom_status_code_and_message():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/custom", lambda r: nkapi.NKResponse(status=418, body="I'm a teapot"))

    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/custom")
    assert status.startswith("418")
    assert body == b"I'm a teapot"

def test_wsgi_empty_body_and_headers():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/empty", lambda r: nkapi.NKResponse())

    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/empty")
    assert status.startswith("200")
    assert body == b""
    assert isinstance(headers, dict)

def test_wsgi_content_length_is_set_automatically():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/auto", lambda r: nkapi.NKResponse(body="hello"))

    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/auto")
    assert headers.get("Content-Length") == str(len(body))

def test_wsgi_query_parameters_with_special_characters():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/special",
        lambda r: nkapi.NKResponse(body=str(r.query))
    )

    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/special", query="param=hello%20world&emoji=%F0%9F%98%81")
    text = body.decode()
    assert "hello world" in text
    assert "😁" in text

def test_wsgi_large_headers_do_not_break_server():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/headers", lambda r: nkapi.NKResponse(body=r.headers.get("X-Large")))

    large_value = "x" * 10_000
    status, headers, body = run_wsgi_app(server.wsgi_app, "GET", "/headers", headers={"X-Large": large_value})
    assert body.decode() == large_value

def test_wsgi_multiple_routes_same_path_different_methods():
    server = nkapi.NKServer()
    server.router.register(["GET"], "/multi", lambda r: nkapi.NKResponse(body="get"))
    server.router.register(["POST"], "/multi", lambda r: nkapi.NKResponse(body="post"))

    status_get, _, body_get = run_wsgi_app(server.wsgi_app, "GET", "/multi")
    status_post, _, body_post = run_wsgi_app(server.wsgi_app, "POST", "/multi")
    
    assert body_get == b"get"
    assert body_post == b"post"
