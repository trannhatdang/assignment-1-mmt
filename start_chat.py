import subprocess
import time
import sys

SERVER_PORT = 9999
TRACKER_PORT = 9998

def start_tracker():
    print("Starting tracker...")

    server_process = subprocess.Popen([
        sys.executable, 
        'start_tracker_http.py',
        '--port', str(TRACKER_PORT)
    ])
    
    time.sleep(2)
    return server_process

def new_peer(username, port):
    print("Starting peer...")

    peer_process = subprocess.Popen([
        sys.executable,
        'start_client.py',
        '--addr', '0.0.0.0:' + str(port),
        '--username', username,
        '--tracker', '0.0.0.0:' + str(TRACKER_PORT)
    ])

    time.sleep(1)

    return peer_process

if __name__ == "__main__":
    no_tracker = '--no-tracker' in sys.argv

    print("Starting P2P demo...")

    procs = []

    peernames = [
        ['alice', 9000],
        ['bob', 9001],
        ['robo', 9002]
    ]

    try:
        if not no_tracker:
            tracker = start_tracker()
            procs += [tracker]

        procs += [new_peer(p[0], p[1]) for p in peernames]

        for p in peernames:
            print(f"Peer {p[0]} started. Visit http://0.0.0.0:{p[1]}/chat.html")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting...")

        for p in procs:
            p.terminate()

        time.sleep(2)

        for p in procs:
            p.kill()
