class Ticket:
    content: str
    guesses: list[int]
    average: int

    def __init__(self, content: str):
        self.content = content
        self.guesses = []
        self.average = 0
