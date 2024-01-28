import socket
import time
from ticket import Ticket
from person import Person
from roomState import RoomState
from instruction import Instruction
import json
import queue


def udp_broadcast_listener(messageQueue: queue.Queue, heartbeatQueue: queue.Queue, roomQueue: queue.Queue, electionQueue: queue.Queue, phase_queue: queue.Queue, stopQueue: queue.Queue,
                           roomState: RoomState, user: Person, command: str = ""):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(5) #  kann das timeout einfach rausgelassen werden?
    udp_socket.bind(('0.0.0.0', 61424))
    while stopQueue.qsize() == 0:
        data: bytes = bytes()
        addr: any
        try:
            data, addr = udp_socket.recvfrom(4096)
        except socket.timeout:
            print("UDP: Zeitüberschreitung beim Empfangen von Daten.")
            continue
        except socket.error as err:
            print(f"UDP: Received error: {err}")
        receivedInstruction: Instruction = Instruction(**json.loads(data.decode()))
        if receivedInstruction.sender == user.id:  # ToDo: check if this works
            continue
        match receivedInstruction.action:
            case "join":
                messageQueue.put(receivedInstruction)
                person_to_add = Person.from_json(receivedInstruction.body)
                roomState.add_person(person_to_add)
                roomInstruction = Instruction("room", json.dumps(roomState.to_dict(), indent=2), user.id)
                message = json.dumps(roomInstruction, default=vars)
                send_broadcast_message(message, 61424)
            case "room":
                roomQueue.put(receivedInstruction)
            case "heartbeat":
                heartbeatQueue.put(receivedInstruction)
            case "phase":
                phase_queue.put(receivedInstruction)
            case "ticket":
                roomState.add_ticket(Ticket.from_json(receivedInstruction.body))
            case "guess":
                ticket_index: int = int(receivedInstruction.body.split(":")[0])
                ticket_guess: int = int(receivedInstruction.body.split(":")[1])
                if user.isScrumMaster:
                    print(f"\n received guess: {ticket_guess} \n")
                    roomState.guess_ticket(ticket_index, receivedInstruction.sender, ticket_guess)
            case "next_ticket":
                messageQueue.put(receivedInstruction)
            case "elect":
                print(f"received broadcast election {receivedInstruction.body} from {receivedInstruction.sender}")
                if receivedInstruction.body.startswith("elected"):
                    electionQueue.put(receivedInstruction)
            case "port":
                received_port: int = receivedInstruction.body["port"]
                sender: str = receivedInstruction.sender
                for person in roomState.Persons:
                    if person.id == sender:
                        person.set_port(received_port, False)
            case "kick":
                id_to_kick: str = receivedInstruction.body
                roomState.kick_person(id_to_kick, user, electionQueue, phase_queue)
            case "redo":
                if roomState.Phase == "1":
                    phase_queue.put(receivedInstruction)
                elif roomState.Phase == "2":
                    messageQueue.put(receivedInstruction)
            case "average":
                ticket_index: int = int(receivedInstruction.body.split(":")[0])
                ticket_average: float = float(receivedInstruction.body.split(":")[1])
                roomState.Tickets[ticket_index].average = ticket_average
            case _:
                print(f"Empfangene Broadcast-Nachricht von {addr}: {data.decode()}")


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


def tcp_unicast_listener(stopQueue: queue.Queue, person: Person, electionQueue: queue.Queue, seconds_until_problem: int = 5):
    while True:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind(('0.0.0.0', person.port))
        port = tcp_socket.getsockname()[1]
        person.set_port(port, True)
        tcp_socket.listen(1)
        while stopQueue.qsize() == 0:
            try:
                # Akzeptiere eine eingehende Verbindung
                client_socket, address = tcp_socket.accept()
                # Empfange Daten vom Client
                data = client_socket.recv(1024)
                receivedInstruction: Instruction = Instruction(**json.loads(data.decode()))
                electionQueue.put(receivedInstruction)
                client_socket.close()
            except Exception as ex:
                print(f"Exception unicast: {ex}")
                break


def tcp_unicast_sender(ip_address: str, port: int, message: str):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect((ip_address, port))
        tcp_socket.sendall(message.encode('utf-8'))
    finally:
        tcp_socket.close()
