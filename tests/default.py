import json
import nkapi

server = nkapi.NKServer(
    host="0.0.0.0",
    port=8000
)

app = server.wsgi_app

def root(request: nkapi.NKRequest):
    response = nkapi.NKResponse(
        headers={"Content-Type": "application/json"},
        body={
            "method": request.method,
            "path": request.path,
            "query": request.query,
            "headers": request.headers,
            "body": request.body
        }
    )

    # Hacky response body modification to return the response within the response body
    response.body = "Request:\n" + response.body.decode() + "\n\nResponse:\n" + json.dumps({
        "status": response.status,
        "headers": response.headers,
        "body": response.body.decode()
    }, indent=4)
    response.body = response.body.encode("utf-8")
    response.headers["Content-Length"] = str(len(response.body))

    return response

server.router.register(methods=["GET", "POST"], path="/", callback=root)

if __name__ == "__main__":
    server.start()
