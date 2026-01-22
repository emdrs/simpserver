from http import HTTPMethod
from mariadb import Cursor

from router import route


@route("/users", HTTPMethod.GET)
def get_users(cu: Cursor) -> list[dict]:
    query = "SELECT * FROM Users"

    cu.execute(query)
    rows = cu.fetchall()

    return [{"id": row[0], "name": row[1]} for row in rows]
