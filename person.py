class Person:
    id: str
    isScrumMaster: bool

    def __init__(self, id: str, isScrumMaster:bool):
        self.id = id
        self.isScrumMaster = isScrumMaster

    def __str__(self):
        return f"{self.id}"
