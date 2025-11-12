"""
HTTP-based Tracker using WeApRous (WeApRous -> create_backend -> HttpAdapter)

Provides two endpoints:
 - POST /register    -> register peer (body JSON: {"ip":..., "port":...})
 - GET  /peers       -> return JSON list of registered peers

Run with: python start_tracker_http.py --host 0.0.0.0 --port 8000
"""
import argparse
import json
import time

from datetime import datetime

from daemon.weaprous import WeApRous
from common import send_http_request, Address, parse_address, stringify_address
from typing import Dict, Tuple, List, Any

app = WeApRous()

# Keep peers in a dict to avoid duplicates. Key = ip:port
active_peers = {}

"""
TODO: Channel management

- API to present a list of channels
- Accept join requests from peers.
- Present messages to peers' client browser (take in a time value and returns a list of messages newer than said time value)
"""

Message = Tuple[Address, str]

class Channel:
    def __init__(self, name: str):
        self.name = name
        self.connected_peers: List[Address] = []

    def accept_peer(self, addr: Address):
        if addr in self.connected_peers:
            print("Peer already in channel")
            return

        self.connected_peers.append(addr)

    def accept_message(self, sender: Address, message: str):
        if sender not in self.connected_peers:
            print("Peer not in channel")
            return
        
    def __broadcast(self, msg: Message):
        for addr in self.connected_peers:
            try:
                send_http_request(
                    addr,
                    'POST',
                    '/inbox',
                    {"sender": msg[0], "channel": self.name, "message": msg[1]}
                )
            except:
                pass

    def dump(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'peers': [stringify_address(a) for a in self.connected_peers]
        }

    def __str__(self) -> str:
        return self.name

channels = [
    Channel('general'),
    Channel('IT'),
    Channel('Music')
]

@app.route('/register', methods=['POST'])
def register_peer(headers, body):
    try:
        peer_info = json.loads(body or '{}')
        ip = peer_info.get('ip')
        port = peer_info.get('port')
        username = peer_info.get('username', 'unknown')

        if not ip or not port:
            return ({"status": "error", "message": "Missing IP or Port"}, '400 Bad Request')

        peer_id = f"{ip}:{port}"
        if peer_id not in active_peers:
            active_peers[peer_id] = {"id": peer_id, "ip": ip, "port": port, "username": username}
            print(f"Peer mới đăng ký: {peer_id}")

        return ({"status": "success", "message": f"Peer {peer_id} registered"}, '200 OK')
    except json.JSONDecodeError:
        return ({"status": "error", "message": "Invalid JSON body"}, '400 Bad Request')
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')


@app.route('/peers', methods=['GET'])
def get_peers(headers, body):
    try:
        peers = list(active_peers.values())
        return (peers, '200 OK')
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

@app.route('/listchannels', methods=['GET'])
def get_channels(headers, body):
    try:
        global channels
        ch = [str(c) for c in channels]
        return (ch, '200 OK')
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

@app.route('/joinchannel', methods=['POST'])
def join_channels(headers, body):
    try:
        global channels

        print(body)

        data = json.loads(body)
        peeraddr = parse_address(data['addr'])
        channelname = data['channel']

        for c in channels:
            if channelname == c.name:
                c.accept_peer(peeraddr)
                return ({"status": "success", "message": f"Peer {stringify_address(peeraddr)} accepted"}, '200 OK')
            
    except json.JSONDecodeError as e:
        return ({"status": "error", "message": str(e)}, '400 Bad Request')  
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

@app.route('/listchannels', methods=['GET'])
def poll_channel(headers, body):
    try:
        global channels
        return ([c.dump() for c in channels], '200 OK')

    except json.JSONDecodeError as e:
        return ({"status": "error", "message": str(e)}, '400 Bad Request')  
    except Exception as e:
        return ({"status": "error", "message": str(e)}, '500 Internal Server Error')

def main():
    parser = argparse.ArgumentParser(prog='TrackerHTTP', description='Start HTTP tracker')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()

    print(f"Starting Tracker Server at {args.host}:{args.port}...")

    app.prepare_address(args.host, args.port)
    app.run()

if __name__ == '__main__':
    main()
