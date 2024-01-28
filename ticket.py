import json
import threading


class Ticket:
    content: str
    guesses: dict[str, int]
    average: int
    lock: threading.Lock

    def __init__(self, content: str, guesses={}, average=0):
        self.content = content
        self.guesses = guesses
        self.average = average
        self.lock = threading.Lock()

    def to_dict(self):
        ticket_dict = {
            'content': self.content,
            'guesses': self.guesses,
            'average': self.average
        }
        return ticket_dict

    @classmethod
    def from_json(cls, json_str: str):
        ticket_dict = json.loads(json_str)
        content = ticket_dict['content']
        guesses = ticket_dict['guesses']
        average = ticket_dict['average']
        ticket = Ticket(content, guesses, average)
        return ticket

    def guess(self, user: str, guess: int):
        with self.lock:
            self.guesses[user] = guess
