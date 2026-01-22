from functools import wraps
from http import HTTPMethod
from typing import Callable
import inspect

from database import get_connection_and_cursor


_routes: dict[HTTPMethod, dict[str, Callable]] = {}

# Parameters is Any | None.
RouteCallbackReturn = str | dict | list
RouteCallback = Callable[..., RouteCallbackReturn]


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
        params_names = sig.parameters.keys()

        # Params that can be injected
        has_conn = "conn" in params_names
        has_cur = "cur" in params_names
        has_conn_or_cur = has_conn or has_cur
        has_req = "req" in params_names
        has_body = "body" in params_names

        @wraps(func)
        def wrapper(**kwargs) -> RouteCallbackReturn:
            if not has_req: kwargs.pop("req")
            if not has_body: kwargs.pop("body")

            if has_conn_or_cur: # If use cursor or connection, the commit() is executed automatically at the end.
                conn, cur = get_connection_and_cursor()

                if has_conn: kwargs["conn"] = conn
                if has_cur: kwargs["cur"] = cur

                """
                This solves a bug that if get an error with opened connection, the
                server freezes. Why? I dont really know.
                """
                with conn: 
                    with cur:
                        response = func(**kwargs)

                        conn.commit() # Auto committing the db connection.
                        return response

            return func(**kwargs)

        route_add(path, method, wrapper)
        return wrapper

    return decorator

def ensure_body_keys(keys: dict[str, type]):
    def decorator(func: RouteCallback):
        def wrapper(**kwargs) -> RouteCallbackReturn:
            body_names = kwargs["body"].keys()
            body = kwargs["body"]

            for name, t in keys.items():
                if name not in body_names:
                    raise ValueError(f"{name} not in body.")
                if not isinstance(body[name], t):
                    raise ValueError(f"{name} is not {t}.")

            return func(**kwargs)

        return wrapper

    return decorator

@route("/teste", HTTPMethod.GET)
@ensure_body_keys({"name": str})
def teste(body: dict) -> str:
    return f"Opa: {body}"
