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
    if method not in _routes.keys():
        _routes[method] = {path: callback}
        return

    if path in _routes[method].keys():
        raise ValueError(f"Trying to add endpoint: {path} but already exists.")

    _routes[method][path] = callback


def route_get_callback(path: str, method: HTTPMethod) -> RouteCallback | None:
    if method not in _routes.keys() or path not in _routes[method].keys():
        return None

    return _routes[method][path]


def route(path: str, method: HTTPMethod):
    def decorator(func: RouteCallback):
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(**kwargs):
            conn: Connection | None = None
            cur: Cursor | None = None

            if "conn" in sig.parameters.keys():
                if not conn:
                    conn, cur = get_connection_and_cursor()
                kwargs["conn"] = conn
            if "cur" in sig.parameters.keys():
                if not conn:
                    conn, cur = get_connection_and_cursor()
                kwargs["cur"] = cur

            if conn and cur: # If use cursor or connection, the commit() is executed automatically at the end.
                with conn: # If get an error with opened connection, the server freezes.
                    with cur:
                        response = func(**kwargs)
                        conn.commit() # Auto committing the db connection.
                        return response

            return func(**kwargs)

        route_add(path, method, wrapper)
        return wrapper

    return decorator
