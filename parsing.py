def read_request(client):

    request = bytearray()
    while b"\r\n\r\n" not in request:
        chunk = client.recv(1024)
        if not chunk:
            break
        request.extend(chunk)
    return bytes(request)