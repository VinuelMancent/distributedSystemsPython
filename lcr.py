import json

import middleware
from person import Person
from instruction import Instruction
import queue
from roomState import RoomState
from time import sleep


def elect(user: Person, electQueue: queue.Queue, phase_queue: queue.Queue, broadcast_queue: queue.Queue, roomState: RoomState, stop_queue: queue.Queue):
    while stop_queue.qsize() == 0:
        next_person: Person = None
        sleep(0.5)
        with electQueue.mutex:
            electQueue.queue.clear()
        while True:
            electMessage: Instruction = electQueue.get()
            if next_person is None:
                next_person = get_next_user(roomState, user)
            if electMessage.body.startswith("elected"):
                roomState.set_responsible_person(electMessage.body.split(":")[1])
                for person in roomState.Persons:
                    if person.id == electMessage.body.split(":")[1]:
                        person.set_scrum_master(True)
            elif electMessage.body.startswith("highest_id"):
                received_id = electMessage.body.split(":")[1]
                if received_id < user.id:
                    new_elect_message: Instruction = Instruction("elect", f"highest_id:{user.id}", user.id)
                    middleware.tcp_unicast_sender("localhost", next_person.port,
                                                  json.dumps(new_elect_message, default=vars))
                elif received_id > user.id:
                    new_elect_message: Instruction = Instruction("elect", f"highest_id:{received_id}", user.id)
                    middleware.tcp_unicast_sender("localhost", next_person.port,
                                                  json.dumps(new_elect_message, default=vars))
                elif received_id == user.id:
                    user.set_scrum_master(True)
                    elected_instruction: Instruction = Instruction("elect", f"elected:{user.id}", user.id)
                    middleware.send_broadcast_message(json.dumps(elected_instruction, default=vars), 61424)
                    print("You are the new leader")
                    redo_instruction: Instruction = Instruction("redo", "", user.id)
                    broadcast_queue.put(redo_instruction)
                    middleware.send_broadcast_message(json.dumps(redo_instruction, default=vars), 61424)
                    phase_queue.put(redo_instruction)
                    break


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
