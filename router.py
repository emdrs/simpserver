from http import HTTPMethod
from typing import Callable


_routes: dict[HTTPMethod, dict[str, Callable]] = {}

# Parameters is Any | None.
RouteCallback = Callable[..., str | dict | list]

def route_add(path: str, method: HTTPMethod, callback: RouteCallback) -> None:
    _routes.setdefault(method, {})[path] = callback


def route_get_callback(path: str, method: HTTPMethod) -> RouteCallback | None:
    if path not in _routes[method].keys():
        return

    return _routes[method][path]


def route(path: str, method: HTTPMethod):
    def decorator(func: RouteCallback):
        route_add(path, method, func)
        return func

    return decorator
