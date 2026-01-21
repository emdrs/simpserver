from http import HTTPMethod
from typing import Callable


_routes: dict[HTTPMethod, dict[str, Callable]] = {}


def route_add(path: str, method: HTTPMethod, callback: Callable) -> None:
    _routes.setdefault(method, {})[path] = callback


def route_get_callback(path: str, method: HTTPMethod) -> Callable | None:
    if path not in _routes[method].keys():
        return

    return _routes[method][path]


def route(path: str, method: HTTPMethod):
    def decorator(func):
        route_add(path, method, func)
        return func

    return decorator
