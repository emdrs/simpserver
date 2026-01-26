from http import HTTPMethod
from mariadb import Cursor
import string
import random

from exceptions import CredentialsError
from router import ensure_body_keys, ensure_url_params, middleware, route


@route("/users", HTTPMethod.GET)
def get_users(cur: Cursor) -> list[dict]:
    query = "SELECT * FROM Users"

    cur.execute(query)
    rows = cur.fetchall()

    return [{"id": row[0], "name": row[1]} for row in rows]

@route("/user", HTTPMethod.GET)
@ensure_url_params({"id": int})
def get_user(cur: Cursor, url_params: dict) -> list[dict]:
    query = "SELECT * FROM Users WHERE id = ?"

    cur.execute(query, (url_params["id"],))
    rows = cur.fetchall()

    return [{"id": row[0], "name": row[1]} for row in rows]

@route("/register", HTTPMethod.POST)
@ensure_body_keys({"name": str, "password": str})
def add_user(cur: Cursor, body: dict) -> str:
    query = "INSERT INTO Users (name, password) VALUES (?, ?)"

    cur.execute(query, (body["name"], body["password"]))

    return "Usuário criado com sucesso!"

letters_of_token = string.ascii_letters + string.digits + string.punctuation
logins = {}

@route("/login", HTTPMethod.POST)
@ensure_body_keys({"name": str, "password": str})
def login(cur: Cursor, body: dict) -> dict:
    query = "SELECT * FROM Users WHERE name = ? AND password = ?"

    cur.execute(query, (body["name"], body["password"]))

    user = cur.fetchone()

    if not user:
        raise CredentialsError()

    token = "".join(random.sample(letters_of_token, 3))
    logins[token] = user[0]

    return {"token": token}

@route("/user-all", HTTPMethod.POST)
@middleware()
def get_user_all(cur: Cursor, body: dict, user_info: dict) -> dict:
    query = "SELECT * FROM Users WHERE id = ?"

    # cur.execute(query, (logins[body["token"]],))
    # row = cur.fetchone()

    return user_info
