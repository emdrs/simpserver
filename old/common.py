from http import HTTPMethod
import json
from typing import List

from database import get_connection_and_cursor
from exceptions import ItemAlredyExistError, ItemNotFoundError, UnauthorizedError
from handler import RequestHandler
from enum import Enum
import inspect
import functools


class ModelData:
    def dict(self) -> dict:
        return self.__dict__


class Roles(Enum):
    ADMIN = "Admin"
    TEACHER = "Professor"
    RESIDENT = "Residente"

    @staticmethod
    def get_role(role: str) -> "Roles":
        return Roles(role)

    @staticmethod
    def all() -> List["Roles"]:
        return list(Roles)


class UserInfo:
    def __init__(self, id: int, role: Roles, token: str) -> None:
        self.id = id
        self.role = role
        self.token = token


# PAY ATTENTION HERE KKKKKK(LMAO, LOL)
def safe_run(func, args, kwargs: dict, **extra) -> dict | None:
    kwargs = kwargs | extra

    func_params = inspect.signature(func).parameters

    has_kwargs = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in func_params.values()
    )

    secure_kwargs = {}

    if not has_kwargs:
        for k in kwargs.keys():
            if k in func_params.keys():
                secure_kwargs = {**secure_kwargs, k: kwargs[k]}
    else:
        secure_kwargs = kwargs

    return func(*args, **secure_kwargs)


def get_rh(kwargs: dict) -> RequestHandler:
    assert "rh" in kwargs, "rh was not provided"

    rh = kwargs["rh"]

    assert isinstance(rh, RequestHandler), f"rh is not a RequestHandler object, {rh}"

    return rh


def get_body(rh: RequestHandler) -> dict:
    content_length = int(rh.headers.get("Content-Length", 0))
    body_data = rh.rfile.read(content_length).decode("utf-8")
    if not body_data:
        return {}

    body = json.loads(body_data)

    if not isinstance(body, dict):
        raise ValueError("Invalid body")

    return body


def ensure_header_keys(keys_needed: dict[str, type]):
    def decorator(func):
        def wrapper(**kwargs):
            rh = get_rh(kwargs)

            for kn, t in keys_needed.items():
                if kn not in rh.headers:
                    raise ValueError(f"Missing {kn} in header")
                try:
                    t(rh.headers[kn])
                except:
                    raise ValueError(
                        f"Header parameter type error {rh.headers[kn]}:{t}"
                    )

            return safe_run(func, (), kwargs, headers=rh.headers)

        return wrapper

    return decorator


def ensure_body_keys(keys_needed: dict[str, type]):
    def decorator(func):
        def wrapper(**kwargs):
            body = get_body(get_rh(kwargs))

            for kn, t in keys_needed.items():
                if kn not in body:
                    raise ValueError(f"Missing {kn} in body")
                try:
                    t(body[kn])
                except:
                    raise ValueError(f"Body parameter type error {body[kn]}:{t}")

            return safe_run(func, (), kwargs, body=body)

        return wrapper

    return decorator

def route(path: str, method: HTTPMethod):
    def decorator(func):
        setattr(func, "api", (path, method))

        @functools.wraps(func)
        def wrapper(rh, **kwargs):
            conn, cur = get_connection_and_cursor()

            with conn:
                with cur:
                    response = safe_run(func, (), kwargs, rh=rh, conn=conn, cur=cur)
                    conn.commit()
                    return response

        return wrapper

    return decorator


def middleware(*allowedRoles: Roles):
    def decorator(func):
        @ensure_header_keys({"token": str})
        def wrapper(headers: dict, **kwargs):
            from routes.login import getRoleByToken

            token = headers["token"]

            role = getRoleByToken(token, kwargs["cur"])

            if not role:
                raise ValueError("Token expired")

            if role not in allowedRoles:
                raise UnauthorizedError("Você não têm autorização para fazer isso.")

            from routes.login import get_id_by_token

            id = get_id_by_token(token, kwargs["cur"])

            return safe_run(
                func,
                (),
                kwargs,
                user_info=UserInfo(id, role, token) if id else None,
            )

        return wrapper

    return decorator


def prepare_ensure(table: str, column: str, key: str, kwargs: dict) -> list | None:
    assert "cur" in kwargs, "Missing cur in kwargs forgot  @db_connection before?"
    assert "body" in kwargs, "Missing body in kwargs forgot  @body_keys_needed before?"

    kwargs["cur"].execute(
        f"SELECT * FROM {table} WHERE {column} = ?",
        (kwargs["body"][key],),
    )

    return kwargs["cur"].fetchone()


def ensure_exist(table: str, column: str, key: str, error_msg: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            row = prepare_ensure(table, column, key, kwargs)

            if not row:
                raise ItemNotFoundError(error_msg)

            return safe_run(func, args, kwargs, row=row)

        return wrapper

    return decorator


def ensure_not_exist(table: str, column: str, key: str, error_msg: str):
    def decorator(func):
        def wrapper(**kwargs):
            row = prepare_ensure(table, column, key, kwargs)

            if row:
                raise ItemAlredyExistError(error_msg)

            return safe_run(func, (), kwargs, row=row)

        return wrapper

    return decorator
