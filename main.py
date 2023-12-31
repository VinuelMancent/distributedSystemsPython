import json
import sys
import time
import uuid

from middleware import udp_broadcast_listener, send_broadcast_message, send_heartbeat, tcp_unicast_listener
from person import Person
from roomState import RoomState
from ticket import Ticket
from instruction import Instruction
from heartbeat_manager import manage_heartbeats
import threading
import queue

TIME_TIL_RESPONSE_IN_SECONDS = 5

if __name__ == "__main__":
    user = Person(str(uuid.uuid4()), False)
    broadcastPort = 61424
    roomState: RoomState = RoomState(user)
    broadcast_queue = queue.Queue()
    stop_queue = queue.Queue()
    heartbeat_queue = queue.Queue()

    udp_listener_thread = threading.Thread(target=udp_broadcast_listener, args=(broadcast_queue, heartbeat_queue, stop_queue, roomState))
    udp_listener_thread.start()

    tcp_listener_thread = threading.Thread(target=tcp_unicast_listener, args=(stop_queue,))
    tcp_listener_thread.start()

    heartbeat_sender_thread = threading.Thread(target=send_heartbeat, args=(broadcastPort, user))
    heartbeat_sender_thread.start()

    heartbeat_manager_thread = threading.Thread(target= manage_heartbeats, args=(heartbeat_queue, user, roomState))
    heartbeat_manager_thread.start()

    # send join request
    joinInstruction = Instruction("join", user.id)
    message = json.dumps(joinInstruction, default=vars)
    send_broadcast_message(message, broadcastPort)

    # wait for response of the request
    try:
        while True:
            received_message: Instruction = broadcast_queue.get(timeout=TIME_TIL_RESPONSE_IN_SECONDS)
            # ignore my own messages
            if received_message.body != user.id and received_message.action == "room":
                roomState = roomState.from_json(received_message.body)
                print(f"l42: Received message: {received_message.action}:{received_message.body}")
                break
    except queue.Empty:
        print("l45: No message received within the timeout")
        roomState = RoomState(user)
        print("l47: You created a new Room and are the responsible Person")

    #BIS HIER HER WIRD DER RAUM ERSTELLT; ENTWEDER SELBST ODER ER WIRD EMPFANGEN

    if roomState.Responsible.id == user.id:
        while True:
            response = ""
            if len(roomState.Tickets) == 0:
                response = "Y"
            else:
                response = input("l51: Do you want to create a Ticket?(Y/N)") # diese frage erst ab dem zweiten mal stellen, oder einen check einbauen, dass mindestens ein ticket erstellt werden muss
            if response.upper() == "Y":
                ticketContent = input("l53: What is the task of the ticket?")
                ticket: Ticket = Ticket(ticketContent)
                roomState.Tickets.append(ticket)
            else:
                roomState.Phase = "Phase2"
                phaseTwoInstruction: Instruction = Instruction("Phase", "2")
                message = json.dumps(phaseTwoInstruction, default=vars)
                send_broadcast_message(message, broadcastPort)
                break
    else:
        while True:
            received_message: Instruction = broadcast_queue.get()
            print("l65: Waiting for responsible person to go into phase 2")
            # only check for instruction phase 2
            if (received_message.action == "Phase") and (received_message.body == "2"):
                print("l68: Responsible person gave instruction to go into phase 2")
                break

    print("l70: We are now in phase 2")
    for ticket in roomState.Tickets:
        print(f"l72: We are now guessing the ticket '{ticket.content}'")
        while True:
            try:
                question = int(input("l75: What is your guess?"))
                break
            except:
                print("l78: That's not a valid option!")

    print("l80: We are done guessing the tickets, goodbye!")
    threadsRunning = False
    stop_queue.put(threadsRunning)
    stop_queue.put(threadsRunning)
    time.sleep(5)
    sys.exit(0)
