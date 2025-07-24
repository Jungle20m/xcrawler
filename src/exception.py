

class ErrorHeaderNotFound(Exception):
    def __init__(self, message="headers not found"):
        self.message = message
        super().__init__(self.message)
        
class ErrorDataNotFound(Exception):
    def __init__(self, message="data not found or user is private"):
        self.message = message
        super().__init__(self.message)
        
class ErrorTooManyRequest(Exception):
    def __init__(self, message="too many request"):
        self.message = message
        super().__init__(self.message)
        
class ErrorForbidden(Exception):
    def __init__(self, message="forbidden"):
        self.message = message
        super().__init__(self.message)