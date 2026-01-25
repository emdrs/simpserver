from http import HTTPStatus


class APIError(Exception):
    """Error handled by api"""

    def __init__(self, status_code: HTTPStatus, response: dict) -> None:
        self.response = {"error": type(self).__name__} | response
        self.status_code = status_code
        super().__init__()


class BadRequestError(APIError):
    """Bad request error"""

    def __init__(self, response: dict) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, response)


class BodyKeyMissingError(BadRequestError):
    """When a needed key in body is missing"""

    def __init__(self, key_name: str) -> None:
        super().__init__({"key_name": key_name})


class BodyKeyTypeError(BadRequestError):
    """When a type of a body key is wrong"""

    def __init__(self, key_name: str, key_type: type) -> None:
        super().__init__({"key_name": key_name, "type_needed": key_type.__name__})


class UrlParamMissingError(BadRequestError):
    """When a needed param in url is missing"""

    def __init__(self, param_name: str) -> None:
        super().__init__({"param_name": param_name})
