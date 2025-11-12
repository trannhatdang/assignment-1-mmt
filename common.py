import json
import socket
import argparse
from typing import Dict, Tuple, Optional, Any, List
from datetime import datetime

Address = tuple[str, int]

def parse_address(string: str) -> Address:
    spl = list(string.strip().split(':'))
    if len(spl) == 2:
        ip = spl[0]
        port = int(spl[1])
        return (ip, port)
    
    raise Exception("Invalid address string")

def stringify_address(a: Address) -> str:
    return a[0] + ':' + str(a[1])

def send_http_request(addr: Address, method, path, data: Any) -> Any:
    BUFSIZE = 4096

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(addr)

    body = json.dumps(data) if data else ""
    request = "{} {} HTTP/1.1\r\n".format(method, path)
    request += f"Host: {addr[0]}:{addr[1]}\r\n"
    request += "Content-Type: application/json\r\n"
    request += f"Content-Length: {len(body)}\r\n"
    request += f"\r\n{body}"

    s.sendall(request.encode())
    
    res = bytes()
    while True:
        frag = s.recv(BUFSIZE)
        res += frag

        if len(frag) < BUFSIZE:
            break

    s.close()
    del s

    parts = res.decode('utf-8').split('\r\n\r\n', 2)
    if len(parts) < 2:
        return {}

    return json.loads(parts[1])