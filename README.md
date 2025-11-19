# NKAPI

A lightweight general-purpose API framework for Python. Designed to make getting started quick and easy, NKAPI is inspired by Flask and Django but keeps things minimal and straightforward.  

**Version:** 0.1.0

---

## Installation

Install NKAPI via pip (from PyPI, if published):

```python
pip install nkapi
```

Or install directly from source:

```python
git clone https://github.com/nickkipshidze/python-nkapi.git
cd python-nkapi
pip install .
```

---

## Quick Start

Here’s a minimal example of using NKAPI:

```python
import nkapi

server = nkapi.NKServer(host="127.0.0.1", port=8000)

def root(request):
    return nkapi.NKResponse(
        headers={"Content-Type": "application/json"},
        data={
            "methods": request.methods,
            "path": request.path,
            "query": request.query,
            "headers": request.headers,
            "body": request.body
        }
    )

server.router.register(methods=["GET"], path="/", callback=root)
server.start()
```

Start the server and visit `http://127.0.0.1:8000/` in your browser. You will see a JSON response containing the request details.

---

## Core Components

### NKServer

The main server class. Handles routing, request handling, and starting the HTTP server.

**Initialization:**

```python
server = nkapi.NKServer(host="localhost", port=8000, debug=True)
```

- `host`: The host IP to bind to (default: `localhost`)  
- `port`: Port number to listen on (default: `8000`)  
- `debug`: Whether to print debug information to console (default: `True`)  

**Start the server:**

```python
server.start()
```

---

### NKRouter

Handles request routing.

**Register routes:**

```python
server.router.register(methods=["GET"], path="/", callback=some_function)
```

- `methods`: HTTP methods (`GET`, `POST`, etc.)  
- `path`: URL path to match  
- `callback`: Function that receives an `NKRequest` object and returns an `NKResponse`

---

### NKRequest

Represents an HTTP request.

**Attributes:**

- `method`: HTTP method (e.g., `GET`, `POST`)  
- `path`: URL path  
- `query`: Dictionary of query parameters  
- `headers`: Dictionary of HTTP headers  
- `body`: Request body as a string  
- `client_address`: Tuple of client IP and port  

**Example:**

```python
def handler(request):
    print(request.method)
    print(request.path)
    print(request.query)
```

---

### NKResponse

Represents an HTTP response.

**Initialization:**

```python
response = nkapi.NKResponse(
    headers={"Content-Type": "application/json"},
    data={"message": "Hello, World!"},
    status=200
)
```

- `headers`: Dictionary of HTTP headers  
- `data`: Response content (string or dictionary if `Content-Type` is `application/json`)  
- `status`: HTTP status code (default: `200`)  

NKAPI automatically sets the `Content-Length` header and serializes JSON if needed.

---

### NKRequestHandler

Internal class used by NKServer to handle incoming HTTP requests. You typically don’t need to interact with it directly.

---

## Routing Examples

**GET request:**

```python
server.router.register(["GET"], "/hello", lambda req: nkapi.NKResponse(data="Hello!"))
```

**POST request:**

```python
def echo(request):
    return nkapi.NKResponse(data=request.body)

server.router.register(["POST"], "/echo", echo)
```

**404 Handling:**

If a route is not found, NKAPI automatically returns a `404` response.

**500 Handling:**

If an error occurs in a callback, NKAPI automatically returns a `500` response.

---

## Logging

NKAPI logs requests to the console in the following format:

```
<client_ip> - - [timestamp] "METHOD PATH HTTP/version" STATUS -
```

---

## License

MIT License – see `LICENSE` file for details.
