from http.server import HTTPServer
from sys import argv
from handler import RequestHandler
import ssl
from database import get_connection_and_cursor
from os import system, environ

# try:
#     conn, cur = get_connection_and_cursor()
#     conn.close()
#     cur.close()
# except: # If db doesnt exists, create.
#     system("python3 run_sql.py create_db.sql populate_db.sql")

if __name__ == "__main__":
    if len(argv) < 3 or not argv[2].isnumeric():
        print("WRONG USAGE!")
        print("server.py ip port")
        exit(1)

    RequestHandler.initialize()
    server = HTTPServer((argv[1], int(argv[2])), RequestHandler)

    if "-ssl" in argv:
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslctx.check_hostname = False
        sslctx.load_cert_chain(
            certfile=environ["SSL_CERTIFICATE_FILE_PATH"],
            keyfile=environ["SSL_KEYS_FILE_PATH"],
            password=environ.get("SSL_PASSPHRASE") or None,
        )
        server.socket = sslctx.wrap_socket(server.socket, server_side=True)

    print(f"Server started at {argv[1]}:{argv[2]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
