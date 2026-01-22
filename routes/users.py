from http import HTTPMethod
from mariadb import Cursor

from router import route


@route("/users", HTTPMethod.GET)
def get_users(cur: Cursor) -> list[dict]:
    query = "SELECT * FROM Users"

    cur.execute(query)
    rows = cur.fetchall()

    return [{"id": row[0], "name": row[1]} for row in rows]
