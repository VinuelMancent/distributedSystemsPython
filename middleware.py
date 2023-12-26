import uuid
import socket
import threading
from instruction import Instruction
import json
import queue


def udp_broadcast_listener(queue: queue.Queue):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.bind(('0.0.0.0', 61424))

    print("UDP Broadcast Listener gestartet.")
    while True:
        data, addr = udp_socket.recvfrom(1024)
        receivedInstruction: Instruction = json.loads(data.decode(), object_hook=lambda d: Instruction(**d))
        match receivedInstruction.action:
            case "join":
                queue.put(receivedInstruction)
                print(receivedInstruction)
            case "roomState":
                queue.put(receivedInstruction)
                print(receivedInstruction)
            case _:
                print(f"Empfangene Broadcast-Nachricht von {addr}: {data.decode()}")


def send_broadcast_message(message, port):
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.sendto(message.encode(), ('<broadcast>', port))
    broadcast_socket.close()


def tcp_unicast_listener():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('0.0.0.0', 0))
    tcp_socket.listen(1)

    print("TCP Unicast Listener gestartet.")
    while True:
        conn, addr = tcp_socket.accept()
        print(f"Verbindung von {addr}")
        data = conn.recv(1024)
        print(f"Empfangene TCP-Nachricht: {data.decode()}")
        conn.close()