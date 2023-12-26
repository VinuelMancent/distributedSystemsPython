from person import Person
from ticket import Ticket


class RoomState:
    Persons: list[Person]
    Tickets: list[Ticket]
    Phase: str

    def __init__(self):
        self.Persons = []
        self.Tickets = []
        self.Phase = "Phase1"
