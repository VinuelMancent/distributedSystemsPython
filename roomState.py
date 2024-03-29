import json
import logging
import queue
import string

import middleware
from person import Person
from ticket import Ticket
from instruction import Instruction
import threading


class RoomState:
    def __init__(self, responsible_person: Person, persons: list[Person]=[], tickets:list[Ticket]=[], phase="1", current_ticket_index = 0):
        self.Persons = persons
        self.Tickets = tickets
        self.Phase = phase
        self.Responsible = responsible_person
        self.CurrentTicketIndex = current_ticket_index
        self.lock = threading.Lock()

    def to_dict(self):
        return {
            "Persons": [person.to_dict() for person in self.Persons],
            "Tickets": [ticket.to_dict() for ticket in self.Tickets],
            "Phase": self.Phase,
            "Responsible": self.Responsible.to_dict(),
            "CurrentTicketIndex": self.CurrentTicketIndex
        }

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        persons = [Person(**person) for person in data["Persons"]]
        tickets = [Ticket(**ticket) for ticket in data["Tickets"]]
        responsible_person = Person(**data["Responsible"])
        return RoomState(responsible_person, persons, tickets, data["Phase"], data["CurrentTicketIndex"])

    def add_person(self, person):
        with self.lock:
            self.Persons.append(person)

    def kick_person(self, id: str, user: Person, electQueue: queue.Queue, phase_queue: queue.Queue):
        print(f"kicking person {id}")
        for person in self.Persons:
            if person.id == id:
                self.Persons.remove(person)
                if person.isScrumMaster and len(self.Persons) > 1:
                    elect_instruction: Instruction = Instruction("elect", f"highest_id:{0}", user.id) # ToDo: Achtung! Hierdurch denkt jeder er sei der neue Leader
                    electQueue.put(elect_instruction)
                elif person.isScrumMaster and len(self.Persons) == 1:
                    print("You are now the responsible person")
                    self.set_responsible_person(user.id)
                    user.set_scrum_master(True)
                    redo_instruction: Instruction = Instruction("redo", "", user.id)
                    phase_queue.put(redo_instruction)

    def add_ticket(self, ticket):
        with self.lock:
            self.Tickets.append(ticket)

    def change_phase(self, new_phase):
        with self.lock:
            self.Phase = new_phase

    def get_responsible_person(self):
        with self.lock:
            return self.Responsible

    def set_responsible_person(self, id: string):
        with self.lock:
            new_responsible_person: Person
            for person in self.Persons:
                if person.id == id:
                    new_responsible_person = person
            self.Responsible = new_responsible_person

    def guess_ticket(self, index: int, user: str, guess: int):
        with self.lock:
            self.Tickets[index].guess(user, guess)

    def set_ticket_average(self, index: int, average: float):
        with self.lock:
            self.Tickets[index].set_average(average)

    def print_final_tickets(self):
        for ticket in self.Tickets:
            print(ticket)
