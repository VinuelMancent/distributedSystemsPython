import collections
import json
import threading
from instruction import Instruction

class Person:
    id: str
    isScrumMaster: bool
    heartbeat_dict: dict[str,  collections.deque[bool]]
    lock: threading.Lock

    def __init__(self, id: str, isScrumMaster: bool, heartbeat_dict: dict[str, collections.deque[bool]] = dict()):
        self.id = id
        self.isScrumMaster = isScrumMaster
        self.heartbeat_dict = heartbeat_dict
        self.lock = threading.Lock()

    def __str__(self):
        return f"{self.id}"

    def to_dict(self):
        def serialize_deque(d):
            if isinstance(d, collections.deque):
                return list(d)
            else:
                return d

        return {
            "id": self.id,
            "isScrumMaster": self.isScrumMaster,
            "heartbeat_dict": {k: serialize_deque(v) for k, v in self.heartbeat_dict.items()}
        }

    @classmethod
    def from_json(cls, json_string):
        person_dict = json.loads(json_string)
        id = person_dict["id"]
        isScrumMaster = person_dict["isScrumMaster"]
        heartbeat_dict = {k: collections.deque(v) for k, v in person_dict["heartbeat_dict"].items()}
        return Person(id, isScrumMaster, heartbeat_dict)

    def update_heartbeat_dict(self, id: str, status: bool):
        MAX_LENGTH_OF_DEQUE = 5
        with self.lock:
            if id not in self.heartbeat_dict:
                self.heartbeat_dict[id] = collections.deque[bool](maxlen=MAX_LENGTH_OF_DEQUE)
            self.heartbeat_dict[id].append(status)
