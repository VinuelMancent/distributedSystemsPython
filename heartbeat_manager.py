from person import Person
from instruction import Instruction
import queue

TIME_TIL_HEARTBEAT_EXPECTED = 5
def manage_heartbeats(heartbeat_queue: queue.Queue, person: Person):
    try:
        while True:
            received_message: Instruction = heartbeat_queue.get(timeout=TIME_TIL_HEARTBEAT_EXPECTED)
            user_id = received_message.body
            # ignore my own messages
            if user_id != person.id:
                person.heartbeat_dict[user_id].append(True)
                break
    except queue.Empty:
        print("l45: No message received within the timeout")
        roomState = RoomState(user)
        print("l47: You created a new Room and are the responsible Person")
