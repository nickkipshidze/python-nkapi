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
    assert request.headers["Content-Type"] == "text/plain; charset=utf-8"
    
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
        body="not json at all"
    )
    assert request.body == b"not json at all"
    
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
