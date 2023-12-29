import socket
from roomState import RoomState
from instruction import Instruction
import json
import queue


def udp_broadcast_listener(messageQueue: queue.Queue, stopQueue: queue.Queue, roomState: RoomState, command: str = ""):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.bind(('0.0.0.0', 61424))

    print("mw14: UDP Broadcast Listener gestartet.")
    while stopQueue.qsize() == 0:
        data, addr = udp_socket.recvfrom(1024)
        receivedInstruction: Instruction = json.loads(data.decode(), object_hook=lambda d: Instruction(**d))
        match receivedInstruction.action:
            case "join":
                messageQueue.put(receivedInstruction)
                roomInstruction = Instruction("room", json.dumps(roomState.to_dict(), indent=2))
                print(f"mw22: roomInstruction: {roomInstruction}")
                message = json.dumps(roomInstruction, default=vars)
                send_broadcast_message(message, 61424)
                print(f"mw24: {receivedInstruction}")
            case "room":
                messageQueue.put(receivedInstruction)
                print(f"mw27: {receivedInstruction}")
            case _:
                print(f"mw29: Empfangene Broadcast-Nachricht von {addr}: {data.decode()}")


def send_broadcast_message(message, port):
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.sendto(message.encode(), ('<broadcast>', port))
    broadcast_socket.close()


def tcp_unicast_listener(stopQueue: queue.Queue):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('0.0.0.0', 0))
    tcp_socket.listen(1)

    print("mw44: TCP Unicast Listener gestartet.")
    while stopQueue.qsize() == 0:
        conn, addr = tcp_socket.accept()
        print(f"mw47: Verbindung von {addr}")
        data = conn.recv(1024)
        print(f"mw49: Empfangene TCP-Nachricht: {data.decode()}")
        conn.close()