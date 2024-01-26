import json
import sys
import time
import uuid

import middleware
from middleware import udp_broadcast_listener, send_broadcast_message, send_heartbeat, tcp_unicast_listener
from person import Person
from roomState import RoomState
from ticket import Ticket
from instruction import Instruction
from heartbeat_manager import manage_heartbeats
import threading
import queue
from lcr import *

TIME_TIL_RESPONSE_IN_SECONDS = 0.5

if __name__ == "__main__":
    user = Person(str(uuid.uuid4()), False)
    broadcastPort = 61424
    roomState: RoomState = RoomState(user)
    broadcast_queue = queue.Queue()
    stop_queue = queue.Queue()
    heartbeat_queue = queue.Queue()
    room_queue = queue.Queue()
    election_queue = queue.Queue()
    phase_queue = queue.Queue()

    udp_listener_thread = threading.Thread(target=udp_broadcast_listener,
                                           args=(broadcast_queue, heartbeat_queue, room_queue, election_queue, phase_queue, stop_queue, roomState, user)).start()

    tcp_listener_thread = threading.Thread(target=tcp_unicast_listener, args=(stop_queue, user, election_queue, 5)).start()

    heartbeat_sender_thread = threading.Thread(target=send_heartbeat, args=(broadcastPort, user)).start()

    heartbeat_manager_thread = threading.Thread(target=manage_heartbeats, args=(heartbeat_queue, user, roomState, election_queue, phase_queue)).start()

    election_thread = threading.Thread(target=elect, args=(user, election_queue, phase_queue, roomState)).start()

    # send join request
    joinInstruction = Instruction("join", json.dumps(user.to_dict(), indent=2), user.id)
    message = json.dumps(joinInstruction, default=vars)
    send_broadcast_message(message, broadcastPort)

    print(f"Hello user {user.id} with port {user.port}")
    # wait for response of the request
    try:
        while True:
            received_message: Instruction = room_queue.get(
                timeout=TIME_TIL_RESPONSE_IN_SECONDS)
            # ignore my own messages
            if received_message.sender != user.id and received_message.action == "room":
                received_room_state = roomState.from_json(received_message.body)
                for ticket in received_room_state.Tickets:
                    roomState.add_ticket(ticket)
                for person in received_room_state.Persons:
                    roomState.add_person(person)
                roomState.Responsible = received_room_state.get_responsible_person()
                break
    except queue.Empty:
        user.set_scrum_master(True)
        roomState.add_person(user)
        print("You created a new Room and are the responsible Person")

    # BIS HIER HER WIRD DER RAUM ERSTELLT; ENTWEDER SELBST ODER ER WIRD EMPFANGEN
    while True:
        leave_outer_loop = False
        if user.isScrumMaster:
            response = ""
            if len(roomState.Tickets) == 0:
                response = "Y"
            else:
                response = input("Do you want to create a Ticket?(Y/N)")
            if response.upper() == "Y":
                ticketContent = input("What is the task of the ticket?")
                ticket: Ticket = Ticket(ticketContent)
                roomState.Tickets.append(ticket)
                ticketInstruction: Instruction = Instruction("ticket", json.dumps(ticket.to_dict(), indent=2), user.id)
                message = json.dumps(ticketInstruction, default=vars)
                middleware.send_broadcast_message(message, broadcastPort)
            else:
                roomState.Phase = "2"
                phaseTwoInstruction: Instruction = Instruction("phase", "2", user.id)
                message = json.dumps(phaseTwoInstruction, default=vars)
                send_broadcast_message(message, broadcastPort)
                break
        else:
            print("Waiting for responsible person to go into phase 2")
            while True:
                received_message: Instruction = phase_queue.get()
                # only check for instruction phase 2
                if (received_message.action == "phase") and (received_message.body == "2"):
                    roomState.change_phase("2")
                    print("Responsible person gave instruction to go into phase 2")
                    leave_outer_loop = True
                    break
                elif received_message.action == "redo":
                    break
                else:
                    print("received something else")
                    continue
            else:
                continue
            if leave_outer_loop:
                break

    print("We are now in phase 2")

    # this only works for normal user, not for responsible
    index = 0
    print(f"We are going to guess {len(roomState.Tickets)} tickets")
    for index in range(len(roomState.Tickets)):
        if not user.isScrumMaster:
            while True:
                print("Waiting for responsible person to go to the next ticket") # wird wieder mehrfach ausgegeben je nach user index
                received_message: Instruction = broadcast_queue.get()
                # only check for instruction phase 2
                if received_message.action == "next_ticket":
                    ticket = roomState.Tickets[index]
                    index += 1
                    print(f"We are now guessing the ticket '{ticket.content}'")
                    while True:
                        try:
                            guess = int(input("What is your guess?"))
                            break
                        except:
                            print("That's not a valid option!")
                    break
                elif received_message.action == "redo":
                    print("redoing a ticket")
                    break
        else:
            ticket = roomState.Tickets[index]
            next_ticket_instruction: Instruction = Instruction("next_ticket", "", user.id)
            message = json.dumps(next_ticket_instruction, default=vars)
            send_broadcast_message(message, broadcastPort)
            index += 1
            print(f"Your team is currently guessing the ticket '{ticket.content}'")
            if index < len(roomState.Tickets):
                input("press Enter when you want to go to the next Ticket")
            else:
                input("press Enter to finish")

    print("We are done guessing the tickets, goodbye!")
    threadsRunning = False
    stop_queue.put(threadsRunning)
    stop_queue.put(threadsRunning)
    time.sleep(5)
    sys.exit(0)
