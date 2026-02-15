from http import HTTPMethod
from typing import Callable
import inspect

from .database import get_connection_and_cursor
from .exceptions import *


_routes: dict[HTTPMethod, dict[str, Callable]] = {}

class html(str): pass

# Parameters is Any | None.
RouteCallbackReturn = str | dict | list | html
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
        self.has_conn        = "conn"        in self.params_names
        self.has_cur         = "cur"         in self.params_names
        self.has_conn_or_cur = self.has_conn or self.has_cur
        self.has_req         = "req"         in self.params_names
        self.has_body        = "body"        in self.params_names
        self.has_kwargs      = "body"        in self.params_names
        self.has_url_params  = "url_params"  in self.params_names
        self.has_user_info   = "user_info"   in self.params_names


unsafe_functions: dict[RouteCallback, FunctionSignature] = {}


def safe_run(func: RouteCallback, params: dict) -> RouteCallbackReturn:
    if func not in unsafe_functions:
        unsafe_functions[func] = FunctionSignature(func)

    func_sig = unsafe_functions[func]

    if func.__closure__ == None:
        if not func_sig.has_req       : params.pop("req")
        if not func_sig.has_body      : params.pop("body")
        if not func_sig.has_url_params: params.pop("url_params")
        if not func_sig.has_user_info : params.pop("user_info", None)
        if not func_sig.has_conn      : params.pop("conn", None)
        if not func_sig.has_cur       : params.pop("cur", None)

    # TODO: Check user_info breaks this below
    if (
        func_sig.has_conn_or_cur    and
        "conn" not in params.keys() and
        "cur"  not in params.keys() and
        not func_sig.has_user_info
    ):

        conn, cur = get_connection_and_cursor()

        if func_sig.has_conn: params["conn"] = conn
        if func_sig.has_cur : params["cur"]  = cur

        """
        This solves a bug that if get an error with opened connection, the
        server freezes. Why? Because was not closed? I dont know.
        """
        with conn: 
            with cur:
                response = func(**params)
                return response

    return func(**params)


def route(path: str, method: HTTPMethod):
    def decorator(func: RouteCallback):
        def wrapper(**kwargs) -> RouteCallbackReturn:
            return safe_run(func, kwargs)

        route_add(path, method, wrapper)
        return wrapper

    return decorator


def ensure_body_keys(keys: dict[str, type]):
    def decorator(func: RouteCallback):
        def wrapper(**kwargs) -> RouteCallbackReturn:
            body = kwargs["body"]
            body_names = body.keys()

            for name, t in keys.items():
                if name not in body_names: raise BodyKeyMissingError(name)

                try: body[name] = t(body[name])
                except: raise BodyKeyTypeError(name, t)

            return safe_run(func, kwargs)

        return wrapper

    return decorator


def ensure_url_params(params: dict[str, type]):
    def decorator(func: RouteCallback):
        def wrapper(**kwargs) -> RouteCallbackReturn:
            url_params = kwargs["url_params"]
            url_params_names = url_params.keys()

            for name, t in params.items():
                if name not in url_params_names:
                    raise UrlParamMissingError(name)
                try:
                    url_params[name] = t(url_params[name])
                except:
                    raise UrlParamTypeError(name, t)

            return safe_run(func, kwargs)

        return wrapper

    return decorator


def ensure_exists_in_db_by_body(table: str, pk_name: str, body_key_pk_value: str):
    def decorator(func: RouteCallback):
        @ensure_body_keys({body_key_pk_value: str})
        def wrapper(cur, body, **kwargs) -> RouteCallbackReturn:
            cur.execute(f"SELECT * FROM {table} WHERE {pk_name} = ?",
                        (body[body_key_pk_value],))

            if not cur.fetchone(): raise DoNotExistsInDatabaseError(table)

            return safe_run(func, kwargs | {"cur": cur, "body": body})

        return wrapper

    return decorator

def middleware():
    def decorator(func: RouteCallback):
        @ensure_body_keys({"token": str})
        def wrapper(**kwargs) -> RouteCallbackReturn:
            from routes.users import logins

            if kwargs["body"]["token"] not in logins.keys():
                raise InvalidTokenError()

            func_sig = unsafe_functions[func]

            if func_sig.has_user_info:
                conn, cur = get_connection_and_cursor()
                kwargs["conn"] = conn
                kwargs["cur"] = cur

                cur.execute("SELECT * FROM Users WHERE id = ?", (logins[kwargs["body"]["token"]],))
                row = cur.fetchone()

                kwargs["user_info"] = {"id": row[0], "name": row[1], "password": row[2]}

                with conn: 
                    with cur:
                        return safe_run(func, kwargs)

            return safe_run(func, kwargs)

        return wrapper

    return decorator
