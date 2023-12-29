from roomState import RoomState
from person import Person
from ticket import Ticket
import json


def roomstate_object_hook(obj):
    # Überprüfe, ob das übergebene Objekt ein RoomState ist
    if "__RoomState__" in obj:
        # Erstelle ein RoomState-Objekt mit den Daten im Dictionary
        return RoomState(
            responsiblePerson=obj["Responsible"],
            persons=obj["Persons"],
            tickets=obj["Tickets"],
            phase=obj["Phase"]
        )
    # Überprüfe, ob das übergebene Objekt ein Person ist
    elif "__Person__" in obj:
        # Erstelle ein Person-Objekt mit den Daten im Dictionary
        return Person(id=obj["id"], isScrumMaster=obj["isScrumMaster"])
    # Überprüfe, ob das übergebene Objekt ein Ticket ist
    elif "__Ticket__" in obj:
        # Erstelle ein Ticket-Objekt mit den Daten im Dictionary
        return Ticket(content=obj["content"], guesses=obj["guesses"], average=obj["average"])
    # Wenn das Objekt keine spezielle Behandlung benötigt, gib es unverändert zurück
    return obj