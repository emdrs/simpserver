from functools import wraps
from http import HTTPMethod
from typing import Callable
from mariadb import Connection, Cursor
import inspect

from database import get_connection_and_cursor


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
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(**kwargs):
            conn = None
            cur = None

            for name, param in sig.parameters.items():
                if param.annotation in (Connection, Cursor):
                    if not conn:
                        conn, cur = get_connection_and_cursor()

                    kwargs[name] = conn if param.annotation is Connection else cur

            return func(**kwargs)

        route_add(path, method, wrapper)

        return wrapper

    return decorator
