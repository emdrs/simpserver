from http import HTTPStatus


class APIError(Exception):
    """Error handled by api"""

    def __init__(self, status_code: HTTPStatus, msg: str) -> None:
        self.msg = msg
        self.status_code = status_code
        super().__init__()


class ItemNotFoundError(APIError):
    """When a item does not exist in database"""

    def __init__(self, msg: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class ItemAlredyExistError(APIError):
    """When a item alredy exist in database"""

    def __init__(self, msg: str) -> None:
        super().__init__(HTTPStatus.CONFLICT, msg)


class InvalidCredentialsError(APIError):
    """When user was not found given an email and password"""

    def __init__(self, msg: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, msg)

class UnauthorizedError(APIError):
    """When user doesnt have authorization"""

    def __init__(self, msg: str) -> None:
        super().__init__(HTTPStatus.UNAUTHORIZED, msg)
