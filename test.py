from http import HTTPMethod

from new_router import routes


def route(path: str, method: HTTPMethod):
    def decorator(func):
        routes.setdefault(method, {})[path] = func
        return func
    return decorator


@route("/test", HTTPMethod.GET)
def test() -> str:
    return "Hello, World"
