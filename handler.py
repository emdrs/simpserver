from http import HTTPMethod, HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import BaseServer
from sys import argv
import json

from router import route_get_callback
from routes import * # Registering routes


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

    def run_route(self, method: HTTPMethod) -> str | None:
        route_callback = route_get_callback(self.path, method)

        if not route_callback:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.set_default_headers()
            return

        self.send_response(HTTPStatus.OK)
        self.set_default_headers()

        data = route_callback()

        if isinstance(data, (dict, list)):
            data = json.dumps(data)

        self.wfile.write(data.encode("utf-8"))

    def do_GET(self) -> None:
        self.run_route(HTTPMethod.GET)


def serve_api(ip: str, port: int) -> None:
    server = HTTPServer(((ip, port)), RequestHandler)

    print(f"Running api at: http://{ip}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
