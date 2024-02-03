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
from lcr import elect
from inputimeout import inputimeout


def get_user_input(guess: int, stop: dict[str, bool], broadcast_queue: queue.Queue):
    counter: int = 0
    while not stop["stop"]:
        if counter == 0:
            inputmessage = "What is your guess?"
        else:
            inputmessage = ""
        counter += 1
        try:
            user_guess = int(inputimeout(prompt=inputmessage, timeout=5))
            guess += user_guess
            guessInstruction: Instruction = Instruction("guess", str(index) + ":" + str(guess), user.id)
            middleware.send_broadcast_message(json.dumps(guessInstruction, default=vars), 61424)
            broadcast_queue.put(guessInstruction)
            break
        except Exception as ex:
            if type(ex).__name__ == "ValueError":
                print("That's not a valid option!")


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
                                           args=(
                                           broadcast_queue, heartbeat_queue, room_queue, election_queue, phase_queue,
                                           stop_queue, roomState, user))
    udp_listener_thread.start()

    tcp_listener_thread = threading.Thread(target=tcp_unicast_listener, args=(stop_queue, user, election_queue, 5))
    tcp_listener_thread.start()

    heartbeat_sender_thread = threading.Thread(target=send_heartbeat, args=(broadcastPort, user, stop_queue))
    heartbeat_sender_thread.start()

    heartbeat_manager_thread = threading.Thread(target=manage_heartbeats, args=(
    heartbeat_queue, user, roomState, election_queue, phase_queue, stop_queue))
    heartbeat_manager_thread.start()

    election_thread = threading.Thread(target=elect,
                                       args=(user, election_queue, phase_queue, broadcast_queue, roomState, stop_queue))
    election_thread.start()

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
                # roomState.Responsible = received_room_state.get_responsible_person()
                roomState.set_responsible_person(received_room_state.get_responsible_person().id)
                roomState.Phase = received_room_state.Phase
                roomState.CurrentTicketIndex = received_room_state.CurrentTicketIndex
                break

    except queue.Empty:
        user.set_scrum_master(True)
        roomState.add_person(user)
        print("You created a new Room and are the responsible Person")

    if roomState.Phase == "1":
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
                    ticketInstruction: Instruction = Instruction("ticket", json.dumps(ticket.to_dict(), indent=2),
                                                                 user.id)
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

    print(f"We are going to guess {len(roomState.Tickets)} tickets")
    index: int = roomState.CurrentTicketIndex

    while roomState.CurrentTicketIndex < len(roomState.Tickets):
        print(f"we are in round {roomState.CurrentTicketIndex} of {len(roomState.Tickets)}")
        if not user.isScrumMaster:
            while True:
                last_loop_necessary = True
                if roomState.CurrentTicketIndex != 0:
                    print(
                        "Waiting for responsible person to go to the next ticket")  # wird wieder mehrfach ausgegeben je nach user index
                received_message: Instruction = broadcast_queue.get()
                print(f"received instruction is {received_message.action}")
                # only check for instruction phase 2
                if received_message.action == "next_ticket":
                    ticket = roomState.Tickets[roomState.CurrentTicketIndex]
                    print(f"We are now guessing the ticket '{ticket.content}'")
                    # Here i try to do the user input handling in another thread in order to skip one question when another signal comes in
                    userinput: int = 0
                    stop_user_input_thread: dict[str, bool] = {"stop": False}
                    user_input_thread = threading.Thread(target=get_user_input,
                                                         args=(userinput, stop_user_input_thread, broadcast_queue))
                    user_input_thread.start()
                    while user_input_thread.is_alive():  # check if this condition works
                        try:
                            received_message: Instruction = broadcast_queue.get(timeout=1.0)
                            if received_message.action == "next_ticket":
                                stop_user_input_thread["stop"] = True
                                user_input_thread.join(5.0)
                                last_loop_necessary = False
                                roomState.CurrentTicketIndex += 1
                                broadcast_queue.put(received_message)
                                break
                            elif received_message.action == "guess" and received_message.sender == user.id:
                                stop_user_input_thread["stop"] = True
                                user_input_thread.join(5.0)
                            else:
                                continue
                        finally:
                            continue
                    while last_loop_necessary:
                        try:
                            received_message: Instruction = broadcast_queue.get()
                            if received_message.action == "redo":
                                roomState.CurrentTicketIndex = roomState.CurrentTicketIndex - 1
                                print("We are reguessing this ticket because of the change of the leader")
                            else:
                                broadcast_queue.put(received_message)
                        finally:
                            roomState.CurrentTicketIndex += 1
                            break
                        break
                    break

        else:
            ticket = roomState.Tickets[roomState.CurrentTicketIndex]
            next_ticket_instruction: Instruction = Instruction("next_ticket", "", user.id)
            message = json.dumps(next_ticket_instruction, default=vars)
            send_broadcast_message(message, broadcastPort)
            print(f"Your team is currently guessing the ticket '{ticket.content}'")
            if roomState.CurrentTicketIndex <= len(roomState.Tickets) - 1:
                next_step_text = "press Enter when you want to go to the next Ticket"
                if roomState.CurrentTicketIndex == len(roomState.Tickets) - 1:  # if there is a ticket after the current one
                    next_step_text = "press Enter to finish"
                input(next_step_text)
                guesses_dict = roomState.Tickets[roomState.CurrentTicketIndex].guesses
                sum_of_guesses: int = 0
                for guess in guesses_dict.values():
                    sum_of_guesses += guess
                average: int = 0
                if len(guesses_dict) > 0:
                    average = sum_of_guesses / len(guesses_dict)
                else:
                    average = 0
                print(f"the final guess of the ticket {ticket.content} is: {average}")
                roomState.set_ticket_average(roomState.CurrentTicketIndex, average)
                averageInstruction: Instruction = Instruction("average", str(roomState.CurrentTicketIndex) + ":" + str(average), user.id)
                middleware.send_broadcast_message(json.dumps(averageInstruction, default=vars), 61424)
                if roomState.CurrentTicketIndex == len(roomState.Tickets) - 1:
                    print("---------------FINAL RESULTS---------------")
                    roomState.print_final_tickets()
                if roomState.CurrentTicketIndex == len(roomState.Tickets) - 1:
                    next_ticket_instruction: Instruction = Instruction("next_ticket", "", user.id)
                    message = json.dumps(next_ticket_instruction, default=vars)
                    send_broadcast_message(message, broadcastPort)
            roomState.CurrentTicketIndex += 1

    print("We are done guessing the tickets, goodbye!")
    threadsRunning = False
    stop_queue.put(threadsRunning)
    time.sleep(5)
    sys.exit(0)
