from http import HTTPMethod
from typing import Any, Callable
import inspect
import re

from .exceptions import *


class Route:
    def __init__(self, original_path: str, callback: RouteCallback) -> None:
        self.original_path = original_path
        self.callback = callback
        self.path = original_path
        self.path_params: dict | None = None

        re_search = re.search("<.*:.*>", self.path)
        re_split = re.split("<.*:.*>", self.path)

        if re_search:
            self.path = ".*".join(re_split)
            param_name, param_type = re_search.group(0)[1:-1].split(":")
            self.path_params = {param_name: param_type}


_routes: dict[HTTPMethod, dict[str, Route]] = {}

class html(str): pass

# Parameters is Any | None.
RouteCallbackReturn = str | dict | list | html
RouteCallback = Callable[..., RouteCallbackReturn]


def route_add(path: str, method: HTTPMethod, callback: RouteCallback) -> None:
    if method not in _routes.keys():
        _routes[method] = {}

    if path in _routes[method].keys():
        raise ValueError(f"Trying to add endpoint: {path} but already exists.")

    route = Route(path, callback)

    _routes[method][route.path] = route


def get_route_info(path: str, method: HTTPMethod) -> Route | None:
    if method not in _routes.keys():
        return None

    if path not in _routes[method].keys():
        for route_path in _routes[method].keys():
            if re.search(route_path, path):
                return _routes[method][route_path]
        return None

    return _routes[method][path]


class FunctionSignature:
    def __init__(self, func: RouteCallback) -> None:
        self.sig             = inspect.signature(func)
        params = self.sig.parameters
        self.params_names    = self.sig.parameters.keys()
        self.has_conn        = "conn"        in self.params_names
        self.has_cur         = "cur"         in self.params_names
        self.has_conn_or_cur = self.has_conn or self.has_cur
        self.has_req         = "req"         in self.params_names
        self.has_body        = "body"        in self.params_names
        self.has_kwargs      = any(
            p.kind == inspect.Parameter.VAR_KEYWORD 
            for p in params.values()
        )
        self.has_url_params  = "url_params"  in self.params_names
        self.has_user_info   = "user_info"   in self.params_names
        self.has_path_params = "path_params" in self.params_names


unsafe_functions: dict[RouteCallback, FunctionSignature] = {}


def safe_run(func: RouteCallback, params: dict) -> RouteCallbackReturn:
    if func not in unsafe_functions:
        unsafe_functions[func] = FunctionSignature(func)

    func_sig = unsafe_functions[func]

    if func_sig.has_conn_or_cur and "conn" not in params:
        from .database import get_connection_and_cursor
        req = params["req"]
        req.conn, req.cur = get_connection_and_cursor()
        params["conn"], params["cur"] = req.conn, req.cur

    safe_params = params if func_sig.has_kwargs else {}

    if func_sig.has_user_info and "user_info" not in params.keys():
        from .config import user_configs
        params["user_info"] = safe_run(user_configs["get_user_info_func"], params)

    if func.__closure__ == None and not func_sig.has_kwargs and not safe_params:
        for param_name in func_sig.params_names:
            safe_params[param_name] = params[param_name]

    return func(**safe_params)


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


def ensure_header_keys(keys: dict[str, type]):
    def decorator(func: RouteCallback):
        def wrapper(**kwargs) -> RouteCallbackReturn:
            header = kwargs["header"]
            header_names = header.keys()

            for name, t in keys.items():
                if name not in header_names: raise HeaderKeyMissingError(name)

                try: header[name] = t(header[name])
                except: raise HeaderKeyTypeError(name, t)

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
        def wrapper(**kwargs) -> RouteCallbackReturn:
            from .config import user_configs

            login_check = user_configs.get("login_check_func", None)

            if not login_check: raise NotImplementedError

            if not login_check(**kwargs):
                raise InvalidTokenError()

            return safe_run(func, kwargs)

        return wrapper

    return decorator
