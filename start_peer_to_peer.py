import socket
import threading
import time
import json
from enum import Enum
from typing import Dict, Tuple, Any
from daemon import WeApRous

INTRODUCE = "0"
CHAT = "1"
BYE = "2"

class Message:
    def __init__(self, typ: str):
        self.typ = typ

    def dump(self):
        return json.dumps(self.__dict__)

class Chat(Message):
    def __init__(self, sender: str, msg: str):
        super().__init__(CHAT)
        self.sender = sender
        self.message = msg
    
    def dump(self):
        return json.dumps(self.__dict__)

class Introduce(Message):
    def __init__(self, name: str):
        super().__init__(INTRODUCE)
        self.name = name

    def dump(self):
        return json.dumps(self.__dict__)
    
class Bye(Message):
    def __init__(self):
        super().__init__(BYE)
    
    def dump(self):
        return json.dumps(self.__dict__)

def decode_message(jsonstr: str) -> Message:
    o = json.loads(jsonstr)
    typ = o.get("typ", "")

    if typ == CHAT:
        return Chat(o["sender"], o["message"])

    if typ == INTRODUCE:
        return Introduce(o["name"])
    
    if typ == BYE:
        return Bye()
    
    raise BaseException("Unknown message received.")

class Peer:
    def __init__(self, name: str, addr):
        self.name = name
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening = True
        self.addr = addr
        self.listener.bind(addr)

        self.peers: Dict[Tuple[str, int], Any] = {}
        self.names: Dict[Tuple[str, int], str] = {}

        threading.Thread(target=self.begin_listening).start()

    def getaddr(self):
        return self.addr

    def getpeername(self, addr):
        return self.names.get(addr, "Unknown Contact")


    def __introduce(self, conn):
        conn.sendall(Introduce(self.name).dump().encode('utf-8'))

    def begin_listening(self):
        self.listener.listen()
        print(f"{self.name} listening at {self.listener.getsockname()}")

        self.listener.settimeout(2.0)

        while self.listening:
            try:
                conn, addr = self.listener.accept()
                print(f"{self.name} Accepted connection from {addr}")
                self.__introduce(conn)
                self.peers[addr] = conn
                threading.Thread(target=self.handle_peer, args=(conn,addr)).start()
            except:
                pass

    def connect_to_peer(self, p: "Peer"):
        addr = p.getaddr()

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(addr)

            print(f"Connected to {addr}")
            self.peers[addr] = client_socket

            self.__introduce(client_socket)

            threading.Thread(target=self.handle_peer, args=(client_socket,addr)).start()

        except ConnectionRefusedError:
            print(f"Connection refused by {addr}")

    def handle_peer(self, conn, addr):

        def recvall(sock) -> str:
            fragments = []
            LENGTH = 4096
            while True: 
                chunk = sock.recv(4096)
                fragments.append(chunk)

                if len(chunk) < LENGTH: 
                    break

            return b"".join(fragments).decode('utf-8')

        while True:
            data = recvall(conn)

            if not data:
                break
            
            decoded = decode_message(data)

            if isinstance(decoded, Chat):
                print(f"{self.name}: {self.getpeername(addr)} says: {decoded.message}")
           
            elif isinstance(decoded, Introduce):
                self.names[addr] = decoded.name

            elif isinstance(decoded, Bye):
                break

        print(f"{self.name}: Peer {self.getpeername(addr)} disconnected.")

        conn.close()
        self.peers[addr] = None

    def broadcast(self, chat: Chat):
        print(f"{self.name} will be broadcasting \"{chat.message}\"...")

        for out in self.peers.values():
            try:
                out.sendall(chat.dump().encode('utf-8'))
            except Exception as e:
                print(f"Error sending to peer {out}: {e}")

    def direct(self, addr, chat: Chat):
        if out := self.peers.get(addr, None):
            try:
                out.sendall(chat.dump().encode('utf-8'))
            except:
                print(f"Error sending to peer {out}.")

            return

        print(f"Peer with {addr} not found.")

    def close(self):
        self.listening = False
        vals = self.peers.values()

        for v in vals:
            if not v:
                continue

            v.sendall(Bye().dump().encode('utf-8'))
            v.close()
        
        self.peers = {}
        self.listener.close()



    def list_connections(self):
        print(f"\n-- Connections with {self.addr} --")
        for i in self.peers.values():
            print(i)
        print(f"-----------------------------------")    




app = WeApRous()



if __name__ == "__main__":
    p1 = Peer("John", ('localhost', 5000))
    p2 = Peer("Bob", ('localhost', 5001))
    p3 = Peer("Alice", ('localhost', 5002))
    p4 = Peer("James", ('localhost', 5003))

    p2.connect_to_peer(p1)
    p2.connect_to_peer(p4)

    p1.connect_to_peer(p3)
    p1.connect_to_peer(p4)

    time.sleep(1)

    p1.list_connections()
    p2.list_connections()
    p3.list_connections()
    p4.list_connections()

    time.sleep(1)

    p2.broadcast(Chat(str(p2.addr), f"Hello from {p2.name}"))

    time.sleep(0.3)

    p1.broadcast(Chat(str(p1.addr), f"Hello from {p1.name}"))

    time.sleep(0.3)

    p3.broadcast(Chat(str(p3.addr), f"Hello from {p3.name}"))

    time.sleep(1)

    p1.direct(('localhost', 6003), Chat(str(p1.addr), "psst"))
    p1.direct(('0.0.0.0', 6007), Chat(str(p1.addr), "psst"))
    
    time.sleep(2)

    p1.close()
    p2.close()
    p3.close()
    p4.close()
