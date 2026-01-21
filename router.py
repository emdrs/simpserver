from http import HTTPMethod
from typing import Callable


def route(path: str, method: HTTPMethod):
    def decorator(func):
        routes.setdefault(method, {})[path] = func
        return func
    return decorator


routes: dict[HTTPMethod, dict[str, Callable]] = {
    HTTPMethod.GET: {},
    HTTPMethod.POST: {},
    HTTPMethod.PUT: {},
    HTTPMethod.DELETE: {},
}
