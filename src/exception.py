

class ErrorHeaderNotFound(Exception):
    def __init__(self, message="headers not found"):
        self.message = message
        super().__init__(self.message)