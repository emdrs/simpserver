from http import HTTPMethod, HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import BaseServer
from sys import argv
from new_router import routes

from new_routes import *


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server: BaseServer) -> None:
        super().__init__(request, client_address, server)

    def set_default_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "token, Content-Type")
        self.send_header("Content-Type", "text/html")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path not in routes[HTTPMethod.GET].keys():
            self.send_response(HTTPStatus.NOT_FOUND)
            self.set_default_headers()
            return

        self.send_response(HTTPStatus.OK)
        self.set_default_headers()
        self.wfile.write(routes[HTTPMethod.GET][self.path]().encode("utf-8"))


if __name__ == "__main__":
    if len(argv) < 3 or not argv[2].isnumeric():
        print("WRONG USAGE!")
        print("server.py ip port")
        exit(1)

    server = HTTPServer((argv[1], int(argv[2])), RequestHandler)

    print(f"Running server at: http://{argv[1]}:{argv[2]}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
