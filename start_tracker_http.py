"""
HTTP-based Tracker using WeApRous (WeApRous -> create_backend -> HttpAdapter)

Provides two endpoints:
 - POST /register    -> register peer (body JSON: {"ip":..., "port":...})
 - GET  /peers       -> return JSON list of registered peers

Run with: python start_tracker_http.py --host 0.0.0.0 --port 8000
"""
import argparse
import json
from daemon.weaprous import WeApRous

app = WeApRous()

# Keep peers in a dict to avoid duplicates. Key = ip:port
active_peers = {}


@app.route('/register', methods=['POST'])
def register_peer(headers, body):
    try:
        peer_info = json.loads(body or '{}')
        ip = peer_info.get('ip')
        port = peer_info.get('port')

        if not ip or not port:
            return ({"status": "error", "message": "Missing IP or Port"}, '400 Bad Request')

        peer_id = f"{ip}:{port}"
        if peer_id not in active_peers:
            active_peers[peer_id] = {"id": peer_id, "ip": ip, "port": port}
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
