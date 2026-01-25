from http import HTTPMethod
from mariadb import Cursor

from router import ensure_body_keys, ensure_url_params, route


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

@route("/users", HTTPMethod.POST)
@ensure_body_keys({"name": str})
def add_user(cur: Cursor, body: dict) -> str:
    query = "INSERT INTO Users (name) VALUES (?)"

    cur.execute(query, (body["name"],))

    return "Usuário criado com sucesso!"
