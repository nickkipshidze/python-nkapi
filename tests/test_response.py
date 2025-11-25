import nkapi
import json

def test_response_plain_text_defaults_and_encoding():
    request = nkapi.NKResponse(body="hello")
    assert request.status == 200
    assert request.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert request.body == b"hello"
    assert request.headers["Content-Length"] == "5"
    
def test_response_json_auto_serialization_from_dict():
    data = {"a": 1, "b": 2}
    request = nkapi.NKResponse(
        headers={"Content-Type": "application/json"},
        body=data
    )
    decoded = json.loads(request.body.decode("utf-8"))
    assert decoded == data
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["Content-Length"] == str(len(request.body))
    
def test_response_json_auto_serialization_from_list():
    array = [1, 2, 3]
    request = nkapi.NKResponse(
        headers={"Content-Type": "application/json"},
        body=array
    )
    assert json.loads(request.body.decode("utf-8")) == array
    
def test_response_with_bytes_body_does_not_modify_bytes():
    raw = b"\x00\x01binary\xff"
    request = nkapi.NKResponse(body=raw)
    assert request.body == raw
    assert request.headers["Content-Length"] == str(len(raw))
    assert request.headers["Content-Type"] == "application/octet-stream"
    
def test_response_preserves_explicit_content_type_with_plain_text():
    request = nkapi.NKResponse(
        headers={"Content-Type": "text/html"},
        body="<b>hi</b>"
    )
    assert request.headers["Content-Type"] == "text/html"
    assert request.body == b"<b>hi</b>"
    
def test_response_non_json_body_with_json_header_stays_literal():
    request = nkapi.NKResponse(
        headers={"Content-Type": "application/json"},
        body="<h1>not json at all</h1>"
    )
    assert request.body == b"<h1>not json at all</h1>"
    
def test_response_json_header_case_insensitive():
    request = nkapi.NKResponse(
        headers={"content-type": "Application/JSON"},
        body={"x": 1}
    )
    assert json.loads(request.body.decode("utf-8")) == {"x": 1}
    
def test_response_empty_body_and_nondefault_status():
    request = nkapi.NKResponse(body="", status=404)
    assert request.status == 404
    assert request.body == b""
    assert request.headers["Content-Length"] == "0"
    
def test_response_overwrites_content_length_on_given_header():
    request = nkapi.NKResponse(
        headers={"Content-Length": "999"},
        body="hello"
    )
    assert request.headers["Content-Length"] == "5"
    
def test_response_with_weird_unicode_body_encodes_utf8():
    text = "🔥💀漢字"
    request = nkapi.NKResponse(body=text)
    assert request.body == text.encode("utf-8")
    assert request.headers["Content-Length"] == str(len(text.encode("utf-8")))
    
def test_response_with_non_primitive_body_type():
    class X:
        pass
    obj = X()
    request = nkapi.NKResponse(body=str(obj))
    assert isinstance(request.body, bytes)

def test_response_none_body_defaults_to_empty_bytes():
    response = nkapi.NKResponse(body=None)
    assert response.body == b""
    assert response.headers["Content-Length"] == "0"

def test_response_numeric_body_serializes_to_text():
    response = nkapi.NKResponse(body=12345)
    assert response.body == b"12345"
    assert response.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert response.headers["Content-Length"] == str(len(response.body))

def test_response_boolean_body_serializes_to_text():
    response = nkapi.NKResponse(body=True)
    assert response.body == b"True"
    assert response.headers["Content-Length"] == str(len(b"True"))

def test_response_list_with_non_json_content_type_remains_literal():
    data = [1, 2, 3]
    response = nkapi.NKResponse(body=data, headers={"Content-Type": "text/plain"})
    assert response.body == str(data).encode("utf-8")
    assert response.headers["Content-Type"] == "text/plain"

def test_response_dict_with_non_standard_content_type_remains_literal():
    data = {"x": 1}
    response = nkapi.NKResponse(body=data, headers={"Content-Type": "application/custom"})
    assert response.body == str(data).encode("utf-8")
    assert response.headers["Content-Type"] == "application/custom"

def test_response_bytes_with_json_content_type_stays_bytes():
    raw = b"\x00\x01abc"
    response = nkapi.NKResponse(body=raw, headers={"Content-Type": "application/json"})
    assert response.body == raw
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["Content-Length"] == str(len(raw))

def test_response_very_large_body_sets_correct_content_length():
    large = b"x" * 10_000_000
    response = nkapi.NKResponse(body=large)
    assert response.body == large
    assert response.headers["Content-Length"] == str(len(large))

def test_response_unicode_bytes_mixed_encodes_only_utf8_strings():
    mixed = "hello🔥".encode("utf-8") + b"\xff"
    response = nkapi.NKResponse(body=mixed)
    assert response.body == mixed
    assert response.headers["Content-Type"] == "application/octet-stream"

def test_response_custom_headers_preserved_and_normalized():
    response = nkapi.NKResponse(body="ok", headers={"X-Custom": "Value", "content-type": "text/html"})
    assert response.headers["X-Custom"] == "Value"
    assert response.headers["Content-Type"] == "text/html"
    assert response.headers["Content-Length"] == str(len(b"ok"))

def test_response_body_subclass_of_bytes_remains_bytes():
    class MyBytes(bytes):
        pass
    raw = MyBytes(b"abc")
    response = nkapi.NKResponse(body=raw)
    assert isinstance(response.body, bytes)
    assert response.body == raw

def test_response_body_subclass_of_str_encodes_utf8():
    class MyStr(str):
        pass
    text = MyStr("text🔥")
    response = nkapi.NKResponse(body=text)
    assert response.body == text.encode("utf-8")
    assert response.headers["Content-Length"] == str(len(response.body))

def test_response_body_override_status_and_headers_preserves_content_length():
    response = nkapi.NKResponse(body="override", status=201, headers={"X-Test": "yes"})
    assert response.status == 201
    assert response.headers["X-Test"] == "yes"
    assert response.headers["Content-Length"] == str(len(b"override"))

def test_response_body_non_ascii_bytes_stay_unchanged():
    raw = "漢字🔥".encode("utf-8")
    response = nkapi.NKResponse(body=raw)
    assert response.body == raw
    assert response.headers["Content-Length"] == str(len(raw))

def test_response_body_object_with_str_returns_bytes():
    class Custom:
        def __str__(self):
            return "custom"
    obj = Custom()
    response = nkapi.NKResponse(body=obj)
    assert response.body == b"custom"
    assert response.headers["Content-Length"] == str(len(b"custom"))
