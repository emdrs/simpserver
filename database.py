import mariadb
from os import environ

DB_CONFIG = {
    "host": environ.get("DB_HOST", "127.0.0.1"),
    "port": int(environ.get("DB_PORT", 3306)),
    "user": environ.get("DB_USER", "root"),
    "password": environ.get("DB_PASSWORD", "pass"),
    "database": environ.get("DB_NAME", "teste"),
}


def get_connection_and_cursor() -> tuple[mariadb.Connection, mariadb.Cursor]:
    conn = mariadb.connect(**DB_CONFIG)
    return conn, conn.cursor()
