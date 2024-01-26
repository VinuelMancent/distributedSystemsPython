import collections
import json
import threading
import middleware
from instruction import Instruction


class Person:
    id: str
    isScrumMaster: bool
    heartbeat_dict: dict[str,  collections.deque[bool]]
    lock: threading.Lock
    port: int

    def __init__(self, id: str, isScrumMaster: bool, heartbeat_dict: dict[str, collections.deque[bool]] = dict(), port: int = 0):
        self.id = id
        self.isScrumMaster = isScrumMaster
        self.heartbeat_dict = heartbeat_dict
        self.port = port
        self.lock = threading.Lock()

    def __str__(self):
        return f"{self.id}:{self.port}"

    def to_dict(self):
        with self.lock:
            def serialize_deque(d):
                if isinstance(d, collections.deque):
                    return list(d)
                else:
                    return d
            return {
                "id": self.id,
                "isScrumMaster": self.isScrumMaster,
                "port": self.port
            }

    @classmethod
    def from_json(cls, json_string):
        person_dict = json.loads(json_string)
        id = person_dict["id"]
        isScrumMaster = person_dict["isScrumMaster"]
        heartbeat_dict = {}
        port = person_dict["port"]
        return Person(id, isScrumMaster, heartbeat_dict, port)

    def update_heartbeat_dict(self, id: str, status: bool):
        MAX_LENGTH_OF_DEQUE = 5
        with self.lock:
            if not id == self.id:
                if id not in self.heartbeat_dict:
                    self.heartbeat_dict[id] = collections.deque[bool](maxlen=MAX_LENGTH_OF_DEQUE)
                self.heartbeat_dict[id].append(status)

    def remove_person_from_heartbeat_dict(self, id: str):
        with self.lock:
            self.heartbeat_dict.pop(id)

    def set_scrum_master(self, scrumMaster: bool):
        with self.lock:
            self.isScrumMaster = scrumMaster

    def set_port(self, port: int, send: bool):
        with self.lock:
            if port != 0:
                if send and port != self.port:
                    new_port_instruction: Instruction = Instruction("port", {"port": port}, self.id)
                    middleware.send_broadcast_message(json.dumps(new_port_instruction, default=vars), 61424)
                self.port = port
            else:
                print("won't set port to 0")
