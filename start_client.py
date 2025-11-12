#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse
from typing import Dict, Tuple, Optional, Any, List
from datetime import datetime

from daemon.weaprous import WeApRous
from fast_request import send_http_request

PORT = 8000  # Default port
app: WeApRous = WeApRous()
ip = '0.0.0.0'
port = 9000
username = 'guest'
tracker = ('0.0.0.0', 9998)

Address = tuple[str, int]

PEERS_CONNECTED: List[Address] = [] # Connected peers

"""
inbox contains messages: address, message
"""
INBOX_QUEUE: List[Tuple[str, str]] = []

def parse_address(string: str) -> Address:
    spl = list(string.strip().split(':'))
    if len(spl) == 2:
        ip = spl[0]
        port = int(spl[1])
        return (ip, port)
    
    raise Exception("Invalid address string")

def stringify_address(a: Address) -> str:
    return a[0] + ':' + str(a[1])


class Message:
    def __init__(self, sender: Address, receiver: Address, message: str, timecode: datetime = datetime.now()):
        self.sender = sender
        self.receiver = receiver
        self.message = message
        self.timecode = timecode

    def encode(self) -> str:
        return json.dumps({
            'sender': stringify_address(self.sender),
            'receiver': stringify_address(self.receiver),
            'message': self.message,
        })
    
    def dict(self) -> Dict[str, str]:
        return {
            'sender': stringify_address(self.sender),
            'reveiver': stringify_address(self.receiver),
            'message': self.message,
        }

    @staticmethod
    def decode(bytestring: str) -> "Message":
        body = json.loads(bytestring)
        return Message(
            parse_address(body['sender']),
            parse_address(body['receiver']),
            body['message'],
            body['timecode'],
        )

@app.route('/login', methods=['POST'])
def login(headers="admin", body="password"):
    return ({"status": "success", "message": "Alive"}, '200 OK')

@app.route('/list', methods=['GET'])
def listpeers(headers, body):
    res = send_http_request(tracker, "GET", "/peers", {})

    global PEERS_CONNECTED

    for p in res:
        p['connected'] = parse_address(p['id']) in PEERS_CONNECTED

    return res

@app.route('/inbox', methods=['POST'])
def peerinbox(headers, body):
    try:
        data = json.loads(body)
        sender = data['sender']
        message = data['message']

        global INBOX_QUEUE
        INBOX_QUEUE.append((sender, message))
    
        return ({"status": "success", "message": "Message received"}, '200 OK')
    
    except Exception as e:
        return ({"status": "error", "message": f"{e}"}, '200 OK')

@app.route('/pollinbox', methods=['GET'])
def peerpoll(headers, body):
    try:
        global INBOX_QUEUE

        newmsg = INBOX_QUEUE
        msgstr = json.dumps(newmsg)

        INBOX_QUEUE.clear()

        return ({"status": "success", "message": msgstr}, '200 OK')
    
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, '400 Bad Request')
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

@app.route('/send', methods=['POST'])
def peersenddm(headers, body):
    try:
        # print(f"Received request \"{body}\"")
        data = json.loads(body)
        sender = stringify_address((ip, port))
        receiver = data['receiver']
        message = data['message']

        recvaddr = parse_address(receiver)
        
        send_http_request(recvaddr, 'POST', '/inbox', {
            'sender': sender,
            'reveiver': receiver,
            'message': message,
        })

        return ({"status": "success", "message": f"Message send successfully"}, '200 OK')
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, '400 Bad Request')
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

@app.route('/acceptpeer', methods=['POST'])
def acceptpeer(headers, body):
    try:
        global PEERS_CONNECTED

        data = json.loads(body)
    
        addr = parse_address(data)

        PEERS_CONNECTED.append(addr)

        print(f"Accepted connection from {addr}")
        
        return ({"status": "success", "message": f"Connection accepted."}, '200 OK')
    
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, '400 Bad Request')
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

@app.route('/connectpeer', methods=['POST'])
def connectpeer(headers, body):
    try:
        data = json.loads(body)
        toaddr = parse_address(data)
        
        res = send_http_request(toaddr, 'POST', '/acceptpeer', stringify_address((ip, port)))

        print(res)

        if res['status'] != 'success':
            return ({"status": "error", "message": "Peer conection failed"}, '400 Bad Request')

        PEERS_CONNECTED.append(toaddr)

        return ({"status": "success", "message": f"Peer connected successfully"}, '200 OK')
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, '400 Bad Request')
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

@app.route('/get', methods=['GET'])
def get(headers, body):
    return ({"status": "success", "message": {'ip': ip, 'port': port, 'username': username}}, '200 OK')

@app.route('/broadcast', methods=['POST'])
def broadcast(headers, body):
    try:
        data = json.loads(body)
        sender = stringify_address((ip, port))
        message = data['message']

        for recvaddr in PEERS_CONNECTED:
            send_http_request(recvaddr, 'POST', '/inbox', {
                'sender': sender,
                'message': message,
            })

        return ({"status": "success", "message": f"Message send successfully"}, '200 OK')
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, '400 Bad Request')
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

"""
TODO: 
- Dicover and join a channel (sends request to tracker for the list of channels)
- Send a message to channel.
- Poll channels. (watch more new messages)
"""

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default='guest')
    parser.add_argument('--addr', default='0.0.0.0:8000')
    parser.add_argument('--tracker', default='0.0.0.0:9998')
 
    args = parser.parse_args()
    addr = args.addr
    username = args.username

    addr = list(addr.split(':'))
    ip = addr[0].strip()
    port = int(addr[1].strip())

    t = list(args.tracker.split(':'))
    tracker = (t[0].strip(), int(t[1]))

    res = send_http_request(tracker, "POST", "/register", {
        "ip": ip,
        "port": str(port),
        "username": username
    })
    print(f"RES {res}")

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()
