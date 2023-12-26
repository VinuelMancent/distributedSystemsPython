class Instruction:
    action: str
    body: str

    def __init__(self, action: str, body: str):
        self.action = action
        self.body = body

    def __str__(self):
        return f"{self.action}: {self.body}\n"
