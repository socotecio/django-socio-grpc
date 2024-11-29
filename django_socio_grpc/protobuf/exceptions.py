class ProtoRegistrationError(Exception):
    def __init__(self, message: str = None, action: str = None, service: str = None):
        super().__init__(message)
        self.action = action
        self.service = service

    def __str__(self):
        if not self.action or not self.service:
            return super().__str__()
        return f"[{self.service}.{self.action}]{super().__str__()}"


class FromReturnTypeGenerationError(Exception):
    pass


class FutureAnnotationError(FromReturnTypeGenerationError):
    pass


class NoReturnTypeError(FromReturnTypeGenerationError):
    pass


class ListWithMultipleArgsError(FromReturnTypeGenerationError):
    pass


class UnknownTypeError(FromReturnTypeGenerationError):
    def __init__(self, *args: object, return_type) -> None:
        self.return_type = return_type
        super().__init__(*args)


class EnumProtoMismatchError(Exception):
    pass
