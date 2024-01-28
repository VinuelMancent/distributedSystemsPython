import json
import time
from typing import List, Set

import middleware
from person import Person
from instruction import Instruction
import queue
from roomState import RoomState

TIME_TIL_HEARTBEAT_EXPECTED = 5
MISSED_HEARTBEATS_UNTIL_DISCONNECT = 5


def manage_heartbeats(heartbeat_queue: queue.Queue, person: Person, roomState: RoomState, electQueue: queue.Queue, phase_queue: queue.Queue, stop_queue: queue.Queue):
    while stop_queue.qsize() == 0:
        received_heartbeats: set[str] = set()
        amount_of_heartbeats = heartbeat_queue.qsize()
        for heartbeat in range(amount_of_heartbeats):
            heartbeat_instruction: Instruction = heartbeat_queue.get_nowait()
            received_heartbeats.add(heartbeat_instruction.body)
            person.update_heartbeat_dict(heartbeat_instruction.body, True)
        # check if anybody didn't send a heartbeat
        unreceived_heartbeats = get_unassigned_ids(roomState.Persons, received_heartbeats, person)
        for key in unreceived_heartbeats:
            person.update_heartbeat_dict(key, False)
        # check if anybody has only falses in his deque
        ids_to_remove: list[str] = []
        for key in person.heartbeat_dict:
            heartbeat_deque = person.heartbeat_dict[key]
            if heartbeat_deque.count(False) >= MISSED_HEARTBEATS_UNTIL_DISCONNECT:
                ids_to_remove.append(key)
        for id in ids_to_remove:
            kick_instruction: Instruction = Instruction("kick", id, person.id)
            middleware.send_broadcast_message(json.dumps(kick_instruction, default=vars), 61424)
            roomState.kick_person(id, person, electQueue, phase_queue)
            person.remove_person_from_heartbeat_dict(id)
            print(f"Kicked {id} because of missed heartbeats")
        time.sleep(TIME_TIL_HEARTBEAT_EXPECTED)


def get_unassigned_ids(persons: List[Person], ids: Set[str], user: Person) -> List[str]:  # ToDo: Check this method! This should not return the users own id!
    assigned_ids = set(person.id for person in persons)
    unassigned_ids = list(assigned_ids - ids)
    if unassigned_ids.count(user.id) == 1:
        unassigned_ids.remove(user.id)
    return unassigned_ids


def personsToString(persons: List[Person])->str:
    res = ""
    for person in persons:
        res += person.id
        res += " | "
    return res

