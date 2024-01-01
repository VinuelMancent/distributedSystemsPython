import json
import logging
from person import Person
from ticket import Ticket
import threading


class RoomState:
    def __init__(self, responsible_person: Person, persons=None, tickets=None, phase="Phase1"):
        self.Persons = persons or []
        self.Tickets = tickets or []
        self.Phase = phase
        self.Responsible = responsible_person
        self.lock = threading.Lock()

    def to_dict(self):
        return {
            "Persons": [person.to_dict() for person in self.Persons],
            "Tickets": [ticket.__dict__ for ticket in self.Tickets],
            "Phase": self.Phase,
            "Responsible": self.Responsible.to_dict()
        }

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        persons = [Person(**person) for person in data["Persons"]]
        tickets = [Ticket(**ticket) for ticket in data["Tickets"]]
        responsible_person = Person(**data["Responsible"])
        return RoomState(responsible_person, persons, tickets, data["Phase"])

    def add_person(self, person):
        with self.lock:
            self.Persons.append(person)

    def kick_person(self, id):
        with self.lock:
            logging.debug(f"kicking person {id}")
            for person in self.Persons:
                if person.id == id:
                    logging.debug(f"kicking {person}")
                    self.Persons.remove(person)

    def add_ticket(self, ticket):
        with self.lock:
            self.Tickets.append(ticket)

    def change_phase(self, new_phase):
        with self.lock:
            self.Phase = new_phase

    def get_responsible_person(self):
        with self.lock:
            return self.Responsible
