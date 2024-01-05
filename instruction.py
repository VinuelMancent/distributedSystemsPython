class Instruction:
    action: str
    body: str
    sender: str

    def __init__(self, action: str, body: str, sender: str):
        self.action = action
        self.body = body
        self.sender = sender

    def __str__(self):
        return f"{self.action}: {self.body} from {self.sender}\n"
