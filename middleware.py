import socket
import time

from ticket import Ticket
from person import Person
from roomState import RoomState
from instruction import Instruction
import json
import queue


def udp_broadcast_listener(messageQueue: queue.Queue, heartbeatQueue: queue.Queue, stopQueue: queue.Queue,
                           roomState: RoomState, user: Person, command: str = ""):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(5)
    udp_socket.bind(('0.0.0.0', 61424))

    print("UDP Broadcast Listener gestartet.")
    while stopQueue.qsize() == 0:
        data: bytes = bytes()
        addr: any
        try:
            data, addr = udp_socket.recvfrom(2048)
        except socket.timeout:
            print("Zeitüberschreitung beim Empfangen von Daten.")
            continue
        except socket.error as err:
            print(f"Received error: {err}")
        receivedInstruction: Instruction = Instruction(**json.loads(data.decode()))
        if receivedInstruction.sender == user.id:  # ToDo: check if this works
            continue
        match receivedInstruction.action:
            case "join":
                messageQueue.put(receivedInstruction)
                roomState.add_person(Person(receivedInstruction.body, False))
                roomInstruction = Instruction("room", json.dumps(roomState.to_dict(), indent=2), user.id)
                message = json.dumps(roomInstruction, default=vars)
                send_broadcast_message(message, 61424)
            case "room":
                print("received a room instruction")
                messageQueue.put(receivedInstruction)
            case "heartbeat":
                heartbeatQueue.put(receivedInstruction)
            case "phase":
                messageQueue.put(receivedInstruction)
            case "ticket":
                print(f"Received a ticket, adding it to roomstate")
                roomState.add_ticket(Ticket.from_json(receivedInstruction.body))
            case "guess":
                print(receivedInstruction)
            case "next_ticket":
                messageQueue.put(receivedInstruction)
            case _:
                print(f"mw43: Empfangene Broadcast-Nachricht von {addr}: {data.decode()}")


def send_heartbeat(port, person):
    TIME_BETWEEN_HEARTBEATS = 5
    instruction = Instruction("heartbeat", person.id, person.id)
    message = json.dumps(instruction, default=vars)
    while True:
        send_broadcast_message(message, port)
        time.sleep(TIME_BETWEEN_HEARTBEATS)


def send_broadcast_message(message, port):
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.sendto(message.encode(), ('<broadcast>', port))
    broadcast_socket.close()


def tcp_unicast_listener(stopQueue: queue.Queue, timeUntilProblem: int = 5):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('0.0.0.0', 0))
    tcp_socket.listen(1)
    tcp_socket.settimeout(timeUntilProblem)

    print("TCP Unicast Listener gestartet.")
    while stopQueue.qsize() == 0:
        try:
            # Akzeptiere eine eingehende Verbindung
            client_socket, address = tcp_socket.accept()
            print(f'Connection from {address[0]}:{address[1]}')
            # Empfange Daten vom Client
            data = client_socket.recv(1024)
            # Sende eine Antwort an den Client
            client_socket.sendall(b'Hello, world!')
        except socket.timeout:
            print("Timeout beim Empfangen von Daten.")
            break
