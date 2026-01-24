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


class FunctionSignature:
    def __init__(self, func: RouteCallback) -> None:
        self.sig             = inspect.signature(func)
        self.params_names    = self.sig.parameters.keys()
        self.has_conn        = "conn" in self.params_names
        self.has_cur         = "cur"  in self.params_names
        self.has_conn_or_cur = self.has_conn or self.has_cur
        self.has_req         = "req"  in self.params_names
        self.has_body        = "body" in self.params_names
        self.has_kwargs      = "body" in self.params_names

unsafe_functions: dict[RouteCallback, FunctionSignature] = {}


def add_func_sig(func: RouteCallback) -> None:
    if func in unsafe_functions.keys():
        print("[WARNIG] - (Re)adding func to func_signatures")

    func_sig = FunctionSignature(func)

    for t in func_sig.sig.parameters.values():
        if t.kind == inspect.Parameter.VAR_KEYWORD:
            return

    unsafe_functions[func] = func_sig

def safe_run(func: RouteCallback, params: dict) -> RouteCallbackReturn:
    if func not in unsafe_functions.keys():
        return func(**params)

    func_sig = unsafe_functions[func]
    if not func_sig.has_req: params.pop("req")
    if not func_sig.has_body: params.pop("body")

    if func_sig.has_conn_or_cur: # If use cursor or connection, the commit() is executed automatically at the end.
        conn, cur = get_connection_and_cursor()

        if func_sig.has_conn: params["conn"] = conn
        if func_sig.has_cur: params["cur"] = cur

        """
        This solves a bug that if get an error with opened connection, the
        server freezes. Why? Because was not closed? I dont know.
        """
        with conn: 
            with cur:
                response = func(**params)

                conn.commit() # Auto committing the db connection.
                return response

    return func(**params)


def route(path: str, method: HTTPMethod):
    def decorator(func: RouteCallback):
        def wrapper(**kwargs) -> RouteCallbackReturn:
            return safe_run(func, kwargs)

        route_add(path, method, wrapper)

        callback = func
        while callback.__closure__ != None:
            callback = callback.__closure__[0].cell_contents

        add_func_sig(callback)
        return wrapper

    return decorator


def ensure_body_keys(keys: dict[str, type]):
    def decorator(func: RouteCallback):
        def wrapper(**kwargs) -> RouteCallbackReturn:
            body = kwargs["body"]
            body_names = body.keys()

            for name, t in keys.items():
                if name not in body_names:
                    raise ValueError(f"{name} not in body.")
                if not isinstance(body[name], t):
                    raise ValueError(f"{name} is not {t}.")

            return safe_run(func, kwargs)

        return wrapper

    return decorator
