import time
from typing import List, Set
from person import Person
from instruction import Instruction
import queue
from roomState import RoomState

TIME_TIL_HEARTBEAT_EXPECTED = 5
MISSED_HEARTBEATS_UNTIL_DISCONNECT = 5


def manage_heartbeats(heartbeat_queue: queue.Queue, person: Person, roomState: RoomState):

    while True:
        received_heartbeats: set[str] = set()
        amount_of_heartbeats = heartbeat_queue.qsize()
        for heartbeat in range(amount_of_heartbeats):
            heartbeat_instruction: Instruction = heartbeat_queue.get_nowait()
            received_heartbeats.add(heartbeat_instruction.body)
            print(f"hm13: received heartbeat from {heartbeat_instruction.body}")
            person.update_heartbeat_dict(heartbeat_instruction.body, True)
        # check if anybody didn't send a heartbeat
        unreceived_heartbeats = get_unassigned_ids(roomState.Persons, received_heartbeats)
        for key in unreceived_heartbeats:
            person.update_heartbeat_dict(key, False)
        # check if anybody has only falses in his deque
        for key in person.heartbeat_dict:
            heartbeat_deque = person.heartbeat_dict[key]
            print(f"heartbeat_deque of {key}: {heartbeat_deque}")
            if heartbeat_deque.count(False) >= MISSED_HEARTBEATS_UNTIL_DISCONNECT:
                print(f"Kicked {key} because of missed heartbeats")
        time.sleep(TIME_TIL_HEARTBEAT_EXPECTED)


def get_unassigned_ids(persons: List[Person], ids: Set[str]) -> List[str]:  # ToDo: Check this method!
    assigned_ids = set(person.id for person in persons)
    return list(assigned_ids - ids)
