from functools import wraps
from http import HTTPMethod
from typing import Callable, get_type_hints
from mariadb import Connection, Cursor


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
        type_hints = get_type_hints(func)

        @wraps(func)
        def wrapper(**params):
            for param_name in params.keys():
                expected_type = type_hints.get(param_name)

                if expected_type is Connection:
                    params[param_name] = None
                elif expected_type is Cursor:
                    params[param_name] = None

            return func(**params)

        route_add(path, method, wrapper)

        return wrapper

    return decorator
