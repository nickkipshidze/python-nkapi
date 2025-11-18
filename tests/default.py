import nkapi

server = nkapi.NKServer(
    host="0.0.0.0",
    port=8000
)

def root(request):
    return nkapi.NKResponse(
        headers={"Content-Type": "application/json"},
        data={
            "method": request.method,
            "path": request.path,
            "query": request.query,
            "headers": request.headers,
            "body": request.body
        }
    )

server.router.register(
    method="GET",
    path="/",
    callback=root
)

server.start()
