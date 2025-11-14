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

import argparse
import json
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from common import Address, parse_address, send_http_request, stringify_address
from daemon.weaprous import WeApRous

PORT = 8000  # Default port
app: WeApRous = WeApRous()
ip = "0.0.0.0"
port = 9000
username = "guest"
tracker = ("0.0.0.0", 9998)

PEERS_CONNECTED: List[Address] = []  # Connected peers

"""
inbox contains messages: address, message
"""
INBOX_QUEUE: List[Dict[str, str]] = []


class Message:
    def __init__(
        self,
        sender: Address,
        receiver: Address,
        message: str,
        timecode: datetime = datetime.now(),
    ):
        self.sender = sender
        self.receiver = receiver
        self.message = message
        self.timecode = timecode

    def encode(self) -> str:
        return json.dumps(
            {
                "sender": stringify_address(self.sender),
                "receiver": stringify_address(self.receiver),
                "message": self.message,
            }
        )

    def dict(self) -> Dict[str, str]:
        return {
            "sender": stringify_address(self.sender),
            "reveiver": stringify_address(self.receiver),
            "message": self.message,
        }

    @staticmethod
    def decode(bytestring: str) -> "Message":
        body = json.loads(bytestring)
        return Message(
            parse_address(body["sender"]),
            parse_address(body["receiver"]),
            body["message"],
            body["timecode"],
        )


@app.route("/login", methods=["POST"])
def login(headers="admin", body="password"):
    return ({"status": "success", "message": "Alive"}, "200 OK")


@app.route("/list", methods=["GET"])
def listpeers(headers, body):
    res = send_http_request(tracker, "GET", "/peers", {})

    global PEERS_CONNECTED

    for p in res:
        p["connected"] = parse_address(p["id"]) in PEERS_CONNECTED

    return res


@app.route("/inbox", methods=["POST"])
def peerinbox(headers, body):
    try:
        data = json.loads(body)
        sender = data["sender"]
        message = data["message"]
        channel = data.get("channel", "")

        global INBOX_QUEUE
        INBOX_QUEUE.append({"sender": sender, "message": message, "channel": channel})

        return ({"status": "success", "message": "Message received"}, "200 OK")

    except Exception as e:
        return ({"status": "error", "message": f"{e}"}, "200 OK")


@app.route("/pollinbox", methods=["GET"])
def peerpoll(headers, body):
    try:
        global INBOX_QUEUE

        newmsg = list(INBOX_QUEUE)

        INBOX_QUEUE.clear()

        return (newmsg, "200 OK")

    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, "400 Bad Request")
    except Exception as e:
        return ({"status": "error", "message": str(e)}, "500 Internal Server Error")


@app.route("/send", methods=["POST"])
def peersenddm(headers, body):
    try:
        # print(f"Received request \"{body}\"")
        data = json.loads(body)
        sender = stringify_address((ip, port))
        receiver = data["receiver"]
        message = data["message"]

        recvaddr = parse_address(receiver)

        send_http_request(
            recvaddr,
            "POST",
            "/inbox",
            {
                "sender": sender,
                "reveiver": receiver,
                "message": message,
            },
        )

        return (
            {"status": "success", "message": f"Message send successfully"},
            "200 OK",
        )
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, "400 Bad Request")
    except Exception as e:
        return ({"status": "error", "message": str(e)}, "500 Internal Server Error")


@app.route("/acceptpeer", methods=["POST"])
def acceptpeer(headers, body):
    try:
        global PEERS_CONNECTED

        data = json.loads(body)

        addr = parse_address(data)

        PEERS_CONNECTED.append(addr)

        print(f"Accepted connection from {addr}")

        return ({"status": "success", "message": f"Connection accepted."}, "200 OK")

    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, "400 Bad Request")
    except Exception as e:
        return ({"status": "error", "message": str(e)}, "500 Internal Server Error")


@app.route("/connectpeer", methods=["POST"])
def connectpeer(headers, body):
    try:
        data = json.loads(body)
        toaddr = parse_address(data)

        res = send_http_request(
            toaddr, "POST", "/acceptpeer", stringify_address((ip, port))
        )

        print(res)

        if res["status"] != "success":
            return (
                {"status": "error", "message": "Peer conection failed"},
                "400 Bad Request",
            )

        PEERS_CONNECTED.append(toaddr)

        return (
            {"status": "success", "message": f"Peer connected successfully"},
            "200 OK",
        )
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, "400 Bad Request")
    except Exception as e:
        return ({"status": "error", "message": str(e)}, "500 Internal Server Error")


@app.route("/get", methods=["GET"])
def get(headers, body):
    return ({"ip": ip, "port": port, "username": username}, "200 OK")


@app.route("/broadcast", methods=["POST"])
def broadcast(headers, body):
    try:
        message = body
        sender = stringify_address((ip, port))

        for recvaddr in PEERS_CONNECTED:
            send_http_request(
                recvaddr,
                "POST",
                "/inbox",
                {
                    "sender": sender,
                    "message": message,
                },
            )

        return (
            {"status": "success", "message": f"Message send successfully"},
            "200 OK",
        )
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, "400 Bad Request")
    except Exception as e:
        return ({"status": "error", "message": str(e)}, "500 Internal Server Error")


"""
TODO:
- Dicover and join a channel (sends request to tracker for the list of channels)
- Send a message to channel.
- Poll channels. (watch more new messages)
"""


@app.route("/listchannels", methods=["GET"])
def listchannels(headers, body):
    return send_http_request(tracker, "GET", "/listchannels", {})


@app.route("/joinchannel", methods=["POST"])
def joinchannel(headers, body):
    try:
        print(body)

        addr = stringify_address((ip, port))
        channel = json.loads(body)

        send_http_request(
            tracker, "POST", "/joinchannel", {"addr": addr, "channel": channel}
        )

        return (
            {"status": "success", "message": f"Message send successfully"},
            "200 OK",
        )
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": f"{e}"}, "400 Bad Request")
    except Exception as e:
        return ({"status": "error", "message": str(e)}, "500 Internal Server Error")


@app.route("/sendchannel", methods=["POST"])
def send_channel(headers, body):
    try:
        data = json.loads(body or "{}")
        channel_name = data.get("channel")
        message = data.get("message")

        if not channel_name or message is None:
            return (
                {"status": "error", "message": "Missing channel or message"},
                "400 Bad Request",
            )

        # 1. (Client) Hỏi Tracker để lấy danh sách TẤT CẢ các kênh và thành viên
        all_channels_info = send_http_request(tracker, "GET", "/listchannels", {})

        target_peers = []

        # 2. Tìm kênh (channel) mà chúng ta muốn gửi
        for c_info in all_channels_info:
            if c_info.get("name") == channel_name:
                peer_ids = c_info.get("peers", [])

                for peer_id in peer_ids:
                    try:
                        addr = parse_address(peer_id)
                        # Không gửi tin nhắn cho chính mình
                        if addr != (ip, port):
                            target_peers.append(addr)
                    except Exception as e:
                        print(f"Không thể parse địa chỉ peer: {peer_id}, lỗi: {e}")

                break  # Đã tìm thấy kênh

        if not target_peers:
            print(f"Không tìm thấy peer nào (khác) trong kênh {channel_name} để gửi.")

        # 3. (P2P) Gửi tin nhắn P2P trực tiếp đến tất cả peer trong kênh
        sender_id = stringify_address((ip, port))

        for recv_addr in target_peers:
            try:
                # Gửi thẳng đến API /inbox của peer đó
                send_http_request(
                    recv_addr,
                    "POST",
                    "/inbox",
                    {"sender": sender_id, "message": message, "channel": channel_name},
                )
            except Exception as e:
                print(f"Gửi tin nhắn P2P đến {recv_addr} thất bại: {e}")

        return ({"status": "success", "message": "Message sent to channel"}, "200 OK")

    except json.JSONDecodeError as e:
        return (
            {"status": "error", "message": f"Invalid JSON body: {e}"},
            "400 Bad Request",
        )
    except Exception as e:
        return ({"status": "error", "message": str(e)}, "500 Internal Server Error")


if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="guest")
    parser.add_argument("--addr", default="localhost:8000")
    parser.add_argument("--tracker", default="localhost:9998")

    args = parser.parse_args()
    addr = args.addr
    username = args.username

    addr = list(addr.split(":"))
    ip = addr[0].strip()
    port = int(addr[1].strip())

    t = list(args.tracker.split(":"))
    tracker = (t[0].strip(), int(t[1]))

    try:
        res = send_http_request(
            tracker,
            "POST",
            "/register",
            {"ip": ip, "port": str(port), "username": username},
        )
        print(f"RES {res}")
    except:
        print("Starting without tracker.")

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()
