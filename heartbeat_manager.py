import time
from typing import List, Set
from person import Person
from instruction import Instruction
import queue
from roomState import RoomState

TIME_TIL_HEARTBEAT_EXPECTED = 5


def manage_heartbeats(heartbeat_queue: queue.Queue, person: Person, roomState: RoomState):
    while True:
        #ToDo: Implement a logic that checks which user did not send a heartbeat and set their last entry to false
        amount_of_heartbeats = heartbeat_queue.qsize()
        print(f"received {amount_of_heartbeats} heartbeats")
        received_heartbeats: set[str] = set()
        for heartbeat in range(amount_of_heartbeats):
            heartbeat_instruction: Instruction = heartbeat_queue.get_nowait()
            received_heartbeats.add(heartbeat_instruction.body)
            print(f"hm13: received heartbeat from {heartbeat_instruction.body}")
            person.update_heartbeat_dict(heartbeat_instruction.body, True)
        # check if anybody didn't send a heartbeat
        unreceived_heartbeats = get_unassigned_ids(roomState.Persons, received_heartbeats)
        print(f"unreceived_heartbeats: {unreceived_heartbeats}")
            # check if anybody has only falses in his dequeue

        time.sleep(TIME_TIL_HEARTBEAT_EXPECTED)

def get_unassigned_ids(persons: List[Person], ids: Set[str]) -> List[str]: # ToDo: Check this method!
    assigned_ids = set(person.id for person in persons)
    return list(ids - assigned_ids)