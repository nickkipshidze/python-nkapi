# NKAPI

A lightweight general-purpose API framework for Python. Designed to make getting started quick and easy, NKAPI is inspired by Flask and Django but keeps things minimal and straightforward.  

**Version:** 0.2.0

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

## Quick Start

Here’s a minimal example of using NKAPI:

```python
import nkapi

server = nkapi.NKServer(
    host="127.0.0.1",
    port=8000
)

app = server.wsgi_app

def root(request: nkapi.NKRequest):
    return nkapi.NKResponse(
        headers={"Content-Type": "application/json"},
        body={
            "method": request.method,
            "path": request.path,
            "query": request.query,
            "headers": request.headers,
            "body": request.body
        }
    )

server.router.register(methods=["GET", "POST"], path="/", view=root)

if __name__ == "__main__":
    server.start()
```

Start the server and visit `http://127.0.0.1:8000/` in your browser. You will see a JSON response containing the request details.

Here's an example on how to use the WSGI app with Gunicorn:
```shell
$ gunicorn -w 4 -b 0.0.0.0 app:app --access-logfile -
```

## Logging

NKAPI logs requests to the console in the following format:

```
<client_ip> - - [timestamp] "METHOD PATH HTTP/version" STATUS -
```

## License

MIT License – see `LICENSE` file for details.
