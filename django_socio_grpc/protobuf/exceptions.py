class ProtoRegistrationError(Exception):
    def __init__(self, message: str = None, action: str = None, service: str = None):
        super().__init__(message)
        self.action = action
        self.service = service

    def __str__(self):
        if not self.action or not self.service:
            return super().__str__()
        return f"[{self.service}.{self.action}]{super().__str__()}"
