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
        body={"request": {
            "method": request.method,
            "path": request.path,
            "query": request.query,
            "headers": request.headers,
            "body": request.body
        }}
    )

    # Hacky response body modification to return the response within the response body
    response._body["response"] = {
        "status": response.status,
        "headers": response.headers,
        "body": response.body.decode()
    }

    return response

def status(request: nkapi.NKRequest):
    code = request.params["code"]
    return nkapi.NKResponse(
        body=f"status code {code}",
        status=int(code)
    )

server.router.register(methods=["GET", "POST"], path="/", view=root)
server.router.register(methods=["GET", "POST"], path="/status/<code>", view=status)

if __name__ == "__main__":
    server.start()
