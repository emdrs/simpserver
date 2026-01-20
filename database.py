import mariadb
from config import DB_CONFIG


def get_connection_and_cursor() -> tuple[mariadb.Connection, mariadb.Cursor]:
    conn = mariadb.connect(**DB_CONFIG)
    return conn, conn.cursor()


def execute_queries(queries):
    conn, cur = get_connection_and_cursor()
    results = []

    try:
        for query, params in queries:
            if query.strip().lower().startswith("select"):
                cur.execute(query, params)
                results.append(cur.fetchall())
            elif query.strip().lower().startswith("insert") and isinstance(
                params[0], list
            ):
                cur.executemany(query, params)
            else:
                cur.execute(query, params)

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
        cur.close()

    return results
