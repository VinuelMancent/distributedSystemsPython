import middleware
from person import Person
from instruction import Instruction
import queue
from roomState import RoomState
from middleware import *


def elect(user: Person, electQueue: queue.Queue, tcpQueue: queue.Queue, roomState: RoomState):
    while True: # ToDo: Idea: what if we do two while True loops so that after a successful election it can elect again?
        electMessage: Instruction = electQueue.get()
        next_person: Person = get_next_user(roomState, user)
        print(f"the next person is {next_person.id} with port {next_person.port}")
        if electMessage.body.startswith("elected"):
            roomState.set_responsible_person(electMessage.body.split(":")[1])
            break
        elif electMessage.body.startswith("highest_id"):
            highest_id = ""
            current_highest_id = electMessage.body.split(":")[1]
            if current_highest_id < user.id:
                highest_id = user.id
            elif current_highest_id > user.id:
                highest_id = current_highest_id
            else:
                electedInstruction: Instruction = Instruction("elect", f"elected:{user.id}", user.id)
                middleware.send_broadcast_message(json.dumps(electedInstruction, default=vars), 61424)
                break
            electMessage.body = f"highest_id:{highest_id}"
            electMessage.sender == user.id
            middleware.tcp_unicast_sender("localhost", next_person.port, json.dumps(electMessage, default=vars))


def get_next_user(roomState: RoomState, user: Person) -> Person:
    roomState.Persons.sort(key=lambda person: person.id)
    index: int = 0
    for person in roomState.Persons:
        if person.id == user.id and index < len(roomState.Persons)-1:
            return roomState.Persons[index+1]
        elif person.id == user.id and index == len(roomState.Persons)-1:
            return roomState.Persons[0]
        index += 1
