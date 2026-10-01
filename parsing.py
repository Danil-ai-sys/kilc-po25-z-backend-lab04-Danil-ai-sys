Name: Sobar Danil 
Group: PO 25-Z 
Date: 1.10.26

def read_request(client):

    request = bytearray()
    while b"\r\n\r\n" not in request:
        chunk = client.recv(1024)
        if not chunk:
            break
        request.extend(chunk)
    return bytes(request)
