import mariadb
from .config import user_configs

def get_connection_and_cursor() -> tuple[mariadb.Connection, mariadb.Cursor]:
    conn = mariadb.connect(**user_configs["DB_CONFIG"])
    return conn, conn.cursor()
