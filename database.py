import mariadb

DB_CONFIG = {
    "host"    : "",
    "port"    : "",
    "user"    : "",
    "password": "",
    "database": "",
}


def set_db_config(host: str, port: int, user: str, password: str, database: str) -> None:
    global DB_CONFIG

    DB_CONFIG = {
        "host"    : host,
        "port"    : port,
        "user"    : user,
        "password": password,
        "database": database,
    }


def get_connection_and_cursor() -> tuple[mariadb.Connection, mariadb.Cursor]:
    conn = mariadb.connect(**DB_CONFIG)
    return conn, conn.cursor()
