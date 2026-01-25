from http import HTTPStatus


class APIError(Exception):
    """Error handled by api"""

    def __init__(self, status_code: HTTPStatus, response: dict) -> None:
        self.response = response
        self.status_code = status_code
        super().__init__()


class BadRequestError(APIError):
    """Bad request error"""

    def __init__(self, response: dict) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, response)


class MissingBodyKeyError(BadRequestError):
    def __init__(self, key: str, msg: str = "Missing key in body") -> None:
        super().__init__({msg: key})


class BodyKeyTypeError(BadRequestError):
    def __init__(
        self, key: str, key_type: type, msg: str = "Wrong key type in body"
    ) -> None:
        super().__init__({msg: (key, key_type.__name__)})


class MissingUrlParamError(MissingBodyKeyError):
    def __init__(self, param: str, msg: str = "Missing param in url") -> None:
        super().__init__(param, msg)
