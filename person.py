import collections
import json
import threading
from instruction import Instruction
from middleware import send_broadcast_message

class Person:
    id: str
    isScrumMaster: bool
    heartbeat_dict: dict[str,  collections.deque[bool]]
    lock: threading.Lock

    def __init__(self, id: str, isScrumMaster: bool):
        self.id = id
        self.isScrumMaster = isScrumMaster
        self.heartbeat_dict = dict()
        self.lock = threading.Lock()

    def __str__(self):
        return f"{self.id}"

    def update_heartbeat_dict(self, id: str, status: bool):
        MAX_LENGTH_OF_DEQUE = 5
        with self.lock:
            if id not in self.heartbeat_dict:
                self.heartbeat_dict[id] = collections.deque[bool](maxlen=MAX_LENGTH_OF_DEQUE)
            self.heartbeat_dict[id].append(status)
            if status == False:
                if self.heartbeat_dict[id].count(False) == MAX_LENGTH_OF_DEQUE:
                    kick_instruction: Instruction = Instruction("kick", id)
                    message = json.dumps(kick_instruction, default=vars)
                    send_broadcast_message(message, 61424)
                    print(f"User {id} has not sent a heartbeat in the near past and will be kicked")
