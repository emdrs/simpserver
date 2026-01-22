from http import HTTPMethod
from mariadb import Cursor

from router import ensure_body_keys, route


@route("/users", HTTPMethod.GET)
def get_users(cur: Cursor) -> list[dict]:
    query = "SELECT * FROM Users"

    cur.execute(query)
    rows = cur.fetchall()

    return [{"id": row[0], "name": row[1]} for row in rows]


@ensure_body_keys({"name": str})
@route("/users", HTTPMethod.POST)
def add_user(cur: Cursor, body: dict) -> dict:
    query = "INSERT INTO Users (name) VALUES (?)"


    # cur.execute(query, (body["name"],))

    return {"message": body["name"]}
    return {"message": "user added successfuly."}
