class UnauthenticatedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class DuplicateModelException(Exception):
    def __init__(self, attribute_name: str, *args: object) -> None:
        super().__init__(*args)
        self.attribute_name = attribute_name