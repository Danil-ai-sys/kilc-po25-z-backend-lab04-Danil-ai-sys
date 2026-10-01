import inspect
import json
import socket

from parsing import read_request
from router import find_route, path_exists


ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
BODY_METHODS = {"POST", "PUT", "PATCH"}
STATUS_TEXT = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    422: "Unprocessable Content",
}


def respond(client, status, headers, body=b""):
    status_line = f"HTTP/1.1 {status} {STATUS_TEXT[status]}\r\n".encode("ascii")
    header_lines = b"".join(
        f"{name}: {value}\r\n".encode("ascii") for name, value in headers.items()
    )
    client.sendall(status_line + header_lines + b"\r\n" + body)


def respond_json(client, status, payload):
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    respond(
        client,
        status,
        {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body)),
            "Connection": "close",
        },
        body,
    )


def _parse_head(head):
    lines = head.decode("iso-8859-1").split("\r\n")
    method, target, protocol = lines[0].split(" ")
    headers = {}
    for line in lines[1:]:
        name, value = line.split(":", 1)
        headers[name.lower()] = value.strip()
    return method, target, protocol, headers


def handle_client(client):
    client.settimeout(5)
    try:
        raw_request = read_request(client)
        if b"\r\n\r\n" not in raw_request:
            respond_json(client, 400, {"detail": "malformed HTTP request"})
            return
        head, body_bytes = raw_request.split(b"\r\n\r\n", 1)
        method, target, _protocol, headers = _parse_head(head)

        if method not in ALLOWED_METHODS:
            respond_json(client, 405, {"detail": "method not allowed"})
            return

        if method in BODY_METHODS:
            content_length = int(headers.get("content-length", "0"))
            while len(body_bytes) < content_length:
                chunk = client.recv(1024)
                if not chunk:
                    break
                body_bytes += chunk
            if len(body_bytes) < content_length:
                respond_json(client, 400, {"detail": "incomplete request body"})
                return

        match = find_route(method, target)
        if match is None:
            status = 405 if path_exists(target) else 404
            detail = "method not allowed" if status == 405 else "route not found"
            respond_json(client, status, {"detail": detail})
            return

        handler, path_parameters = match
        arguments = dict(path_parameters)
        if "body" in inspect.signature(handler).parameters:
            arguments["body"] = body_bytes.decode("utf-8")
        status, payload = handler(**arguments)
        respond_json(client, status, payload)
    except socket.timeout:
        respond_json(client, 408, {"detail": "request timed out"})
    except (UnicodeDecodeError, ValueError) as error:
        respond_json(client, 400, {"detail": str(error)})
    finally:
        client.close()


def run(host="127.0.0.1", port=8080):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen()
        print(f"Listening on http://{host}:{port}")
        while True:
            client, _address = listener.accept()
            handle_client(client)


if __name__ == "__main__":
    run()
