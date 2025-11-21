import nkapi

def default_callback(request):
    return {"ok": True, "params": request.params if request else None}
    
def test_root_route_matches_and_unknown_path_returns_not_found():
    router = nkapi.NKRouter()
    router.register(methods=["GET"], path="/", callback=default_callback)

    assert router.handle(nkapi.NKRequest("GET", "/")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "////")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "/unknown")).status == 404
    
def test_path_normalization_resolves_to_root_or_registered_route():
    router = nkapi.NKRouter()
    router.register(methods=["GET"], path="/", callback=default_callback)
    router.register(methods=["GET"], path="/test", callback=default_callback)

    assert router.handle(nkapi.NKRequest("GET", "/\\/\\/\\/")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "/.")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "/./.")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "/../..")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "/test")) == default_callback(None)

def test_method_mismatch_returns_not_found():
    router = nkapi.NKRouter()
    router.register(methods=["GET"], path="/item", callback=default_callback)

    response = router.handle(nkapi.NKRequest("POST", "/item"))
    assert hasattr(response, "status")
    assert response.status == 404
    
def test_multiple_methods_route_matches_correctly():
    router = nkapi.NKRouter()
    router.register(methods=["GET", "POST"], path="/multi", callback=default_callback)

    assert router.handle(nkapi.NKRequest("GET", "/multi")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("POST", "/multi")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("PUT", "/multi")).status == 404
    
def test_trailing_slashes_do_not_break_routing():
    router = nkapi.NKRouter()
    router.register(methods=["GET"], path="/alpha/beta", callback=default_callback)

    assert router.handle(nkapi.NKRequest("GET", "/alpha/beta/")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "/alpha//beta///")) == default_callback(None)
    
def test_redundant_dots_and_slashes_normalize_correctly():
    router = nkapi.NKRouter()
    router.register(methods=["GET"], path="/path/sub", callback=default_callback)

    assert router.handle(nkapi.NKRequest("GET", "/path/./sub")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "/path////sub")) == default_callback(None)
    assert router.handle(nkapi.NKRequest("GET", "/path/../path/sub")) == default_callback(None)

def test_dynamic_route_extracts_single_parameter_correctly():
    router = nkapi.NKRouter()
    router.register(["GET"], "/user/<id>", default_callback)

    request = nkapi.NKRequest("GET", "/user/123")
    result = router.handle(request)

    assert result["params"] == {"id": "123"}

def test_dynamic_route_with_two_parameters_extracts_all():
    router = nkapi.NKRouter()
    router.register(["GET"], "/shop/<category>/<item>", default_callback)

    request = nkapi.NKRequest("GET", "/shop/books/1984")
    result = router.handle(request)

    assert result["params"] == {"category": "books", "item": "1984"}

def test_static_route_takes_precedence_over_dynamic_route():
    def static(request):
        return "static"

    def dynamic(request):
        return "dynamic"

    router = nkapi.NKRouter()
    router.register(["GET"], "/obj/<id>", dynamic)
    router.register(["GET"], "/obj/list", static)

    request = nkapi.NKRequest("GET", "/obj/list")
    assert router.handle(request) == "static"

    request = nkapi.NKRequest("GET", "/obj/999")
    assert router.handle(request) == "dynamic"
    
def test_dynamic_and_static_segments_mixed_correctly():
    router = nkapi.NKRouter()
    router.register(["GET"], "/a/<mid>/c", default_callback)

    request = nkapi.NKRequest("GET", "/a/xyz/c")
    result = router.handle(request)

    assert result["params"] == {"mid": "xyz"}
    
def test_dynamic_route_not_matching_returns_404():
    router = nkapi.NKRouter()
    router.register(["GET"], "/car/<id>", default_callback)

    request = nkapi.NKRequest("GET", "/car")
    response = router.handle(request)
    assert response.status == 404

    request = nkapi.NKRequest("GET", "/car/1/extra")
    response = router.handle(request)
    assert response.status == 404
    
def test_multiple_methods_on_dynamic_route_dispatch_correctly():
    router = nkapi.NKRouter()
    router.register(["GET", "POST"], "/item/<pk>", default_callback)

    get_r = router.handle(nkapi.NKRequest("GET", "/item/alpha"))
    post_r = router.handle(nkapi.NKRequest("POST", "/item/alpha"))

    assert get_r["params"]["pk"] == "alpha"
    assert post_r["params"]["pk"] == "alpha"

    fail = router.handle(nkapi.NKRequest("PUT", "/item/alpha"))
    assert fail.status == 404
    
def test_dynamic_route_normalization_of_slashes():
    router = nkapi.NKRouter()
    router.register(["GET"], "/x/<y>/z", default_callback)

    request = nkapi.NKRequest("GET", "///x///123///z///")
    response = router.handle(request)

    assert response["params"] == {"y": "123"}
    
def test_dynamic_route_callback_receives_params_before_execution():
    called = {}

    def cb(request):
        called.update(request.params)
        return "done"

    router = nkapi.NKRouter()
    router.register(["GET"], "/user/<uid>/post/<pid>", cb)

    router.handle(nkapi.NKRequest("GET", "/user/u1/post/p9"))

    assert called == {"uid": "u1", "pid": "p9"}
