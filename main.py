import json
import uuid

from middleware import udp_broadcast_listener, send_broadcast_message, tcp_unicast_listener
from person import Person
from roomState import RoomState
from ticket import Ticket
from instruction import Instruction
import threading
import queue

TIME_TIL_RESPONSE_IN_SECONDS = 5

if __name__ == "__main__":
    user = Person(str(uuid.uuid4()), False)
    broadcastPort = 61424
    roomState: RoomState = RoomState(user)
    broadcast_queue = queue.Queue()

    udp_listener_thread = threading.Thread(target=udp_broadcast_listener, args=(broadcast_queue,))
    udp_listener_thread.start()

    tcp_listener_thread = threading.Thread(target=tcp_unicast_listener)
    tcp_listener_thread.start()

    # send join request
    joinInstruction = Instruction("join", user.id)
    message = json.dumps(joinInstruction, default=vars)
    send_broadcast_message(message, broadcastPort)

    # wait for response of the request
    try:
        while True:
            received_message: Instruction = broadcast_queue.get(timeout=TIME_TIL_RESPONSE_IN_SECONDS)
            # ignore my own messages
            if received_message.body != user.id:
                roomState = json.loads(received_message.body, object_hook=lambda d: RoomState(user)) # ToDo: Check if this works
                print(f"Received message: {received_message.action}:{received_message.body}")
                break
    except queue.Empty:
        print("No message received within the timeout")
        roomState = RoomState(user)
        print("You created a new Room and are the responsible Person")

    if roomState.Responsible.id == user.id:
        while True:
            response = input("Do you want to create a Ticket?(Y/N)")
            if response.upper() == "Y":
                ticketContent = input("What is the task of the ticket?")
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
            print("Waiting for responsible person to go into phase 2")
            # only check for instruction phase 2
            if (received_message.action == "Phase") and (received_message.body == "2"):
                print("Responsible person gave instruction to go into phase 2")
                break
    print("We are now in phase 2")
    for ticket in roomState.Tickets:
        print(f"We are now guessing the ticket '{ticket.content}'")
        while True:
            try:
                question = int(input("What is your guess?"))
                break
            except:
                print("That's not a valid option!")

    print("We are done guessing the tickets, goodbye!")
    exit(0)
