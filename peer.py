import socket
import threading
import time
from typing import Dict, Tuple, Any

class Peer:
    def __init__(self, name, addr):
        self.name = name
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = addr
        self.listener.bind(addr)

        self.incoming: Dict[Tuple[str, int], Any] = {}
        self.outgoing: Dict[Tuple[str, int], Any] = {}

        threading.Thread(target=self.begin_listening).start()

    def begin_listening(self):
        self.listener.listen()
        print(f"Listening at {self.listener.getsockname()}")
        while True:
            conn, addr = self.listener.accept()
            print(f"Accepted connection from {addr}")
            self.incoming[addr] = conn
            threading.Thread(target=self.handle_peer, args=(conn,addr)).start()

    def handle_peer(self, conn, addr):
        while True:
            try:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                print(f"{self.name}: {addr} says: {data}")
            except:
                break

        conn.close()
        self.incoming[addr] = None

        print(f"Peer {conn}, disconnected.")

    def connect_to_peer(self, addr):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(addr)

            print(f"Connected to {addr}")
            self.outgoing[addr] = client_socket

            threading.Thread(target=self.handle_peer, args=(client_socket,addr)).start()

        except ConnectionRefusedError:
            print(f"Connection refused by {addr}")

    def broadcast(self, msg):
        print(f"{self.name} will be broadcasting {msg}...")

        for out in self.outgoing.values():
            try:
                out.sendall(msg.encode('utf-8'))
            except:
                print(f"Error sending to peer {out}.")

        for out in self.incoming.values():
            try:
                out.sendall(msg.encode('utf-8'))
            except:
                print(f"Error sending to peer {out}.")

    def direct(self, addr, msg):
        if out := self.outgoing.get(addr, None):
            try:
                out.sendall(msg.encode('utf-8'))
            except:
                print(f"Error sending to peer {out}.")

            return

        print(f"Peer with {addr} not found.")

    def close(self):
        for out in self.outgoing.values():
            out.close()

        for out in self.incoming.values():
            out.close()

        self.outgoing = {}
        self.incoming = {}

    def list_connections(self):
        print(f"\n-- Connections TO {self.addr} --")
        for i in self.incoming.values():
            print(i.getsockname())

        print(f"-- Connections FROM {self.addr} --")
        for i in self.outgoing.values():
            print(i.getsockname())
        print(f"--------------------------------")

if __name__ == "__main__":

    p1 = Peer("p1", ('0.0.0.0', 7000))
    p2 = Peer("p2", ('0.0.0.0', 7001))
    p3 = Peer("p3", ('0.0.0.0', 7002))
    p4 = Peer("p4", ('0.0.0.0', 7003))

    p2.connect_to_peer(('0.0.0.0', 7000))
    p2.connect_to_peer(('0.0.0.0', 7003))

    p1.connect_to_peer(('0.0.0.0', 7002))
    p1.connect_to_peer(('0.0.0.0', 7003))

    time.sleep(1)

    p1.list_connections()
    p2.list_connections()
    p3.list_connections()
    p4.list_connections()

    time.sleep(1)

    p2.broadcast("Hello from 0.0.0.0:7001")

    time.sleep(0.3)

    p1.broadcast("Hello from 0.0.0.0:7000")

    time.sleep(0.3)

    p3.broadcast("Hello from 0.0.0.0:7002")

    time.sleep(1)

    p1.direct(('0.0.0.0', 7003), "psst")
    p1.direct(('0.0.0.0', 7007), "psst")
