import json

import middleware
from person import Person
from instruction import Instruction
import queue
from roomState import RoomState


def elect(user: Person, electQueue: queue.Queue, phase_queue: queue.Queue, roomState: RoomState):
    highest_id: str = user.id
    next_person: Person = None
    while True: # ToDo: Idea: what if we do two while True loops so that after a successful election it can elect again?
        electMessage: Instruction = electQueue.get()
        if next_person is None:
            next_person = get_next_user(roomState, user)
        if electMessage.body.startswith("elected"):
            roomState.set_responsible_person(electMessage.body.split(":")[1])
            for person in roomState.Persons:
                if person.id == electMessage.body.split(":")[1]:
                    person.set_scrum_master(True)
            print(f"person {electMessage.sender} got elected as the new leader")
            break
        elif electMessage.body.startswith("highest_id"):
            received_id = electMessage.body.split(":")[1]
            if received_id < highest_id:
                highest_id = highest_id
            elif received_id > highest_id:
                highest_id = received_id
            elif received_id == user.id:
                user.set_scrum_master(True)
                elected_instruction: Instruction = Instruction("elect", f"elected:{user.id}", user.id)
                middleware.send_broadcast_message(json.dumps(elected_instruction, default=vars), 61424)
                print("I WAS ELECTED!!!!!!!!!!!!!!!!")
                redo_instruction: Instruction = Instruction("redo", "", user.id)
                middleware.send_broadcast_message(json.dumps(redo_instruction, default=vars), 61424)
                phase_queue.put(redo_instruction)
                break
            new_elect_message: Instruction = Instruction("elect", f"highest_id:{highest_id}", user.id)
            middleware.tcp_unicast_sender("localhost", next_person.port, json.dumps(new_elect_message, default=vars))


def get_next_user(roomState: RoomState, user: Person) -> Person:
    roomState.Persons.sort(key=lambda person: person.id)
    index: int = 0
    for person in roomState.Persons:
        if person.id == user.id and index < len(roomState.Persons)-1:
            next_user: Person = roomState.Persons[index+1]
            return next_user
        elif person.id == user.id and index == len(roomState.Persons)-1:
            next_user = roomState.Persons[0]
            return next_user
        index += 1
