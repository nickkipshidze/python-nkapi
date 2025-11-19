import nkapi

server = nkapi.NKServer(
    host="0.0.0.0",
    port=8000
)

app = server.wsgi_app

def root(request: nkapi.NKRequest):
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
    methods=["GET", "POST"],
    path="/",
    callback=root
)

if __name__ == "__main__":
    server.start()
