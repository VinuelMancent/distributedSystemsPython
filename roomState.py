from person import Person
from ticket import Ticket


class RoomState:
    Persons: list[Person]
    Tickets: list[Ticket]
    Phase: str
    Responsible: Person

    def __init__(self, responsiblePerson: Person):
        self.Persons = []
        self.Tickets = []
        self.Phase = "Phase1"
        self.Responsible = responsiblePerson
