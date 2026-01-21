from http import HTTPMethod
from mariadb import Connection, Cursor

from router import route


@route("/users", HTTPMethod.GET)
def get_users(co: Connection, cu: Cursor) -> list[dict]:
    query = "SELECT * FROM Users"

    cu.execute("INSERT INTO Users (name) VALUES ('Manelzaum de Alves Emanuel')")
    co.commit()

    cu.execute(query)
    rows = cu.fetchall()

    return [{"id": row[0], "name": row[1]} for row in rows]
