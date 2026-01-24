from http import HTTPMethod, HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import BaseServer
import json

from router import route_get_callback
from routes import *  # Registering routes


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

    def get_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        body_data = self.rfile.read(content_length).decode("utf-8")
        if not body_data:
            return {}

        body = json.loads(body_data)

        if not isinstance(body, dict):
            raise ValueError("Invalid body")

        return body


    def run_route(self, method: HTTPMethod) -> None:
        route_callback = route_get_callback(self.path, method)

        if not route_callback:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.set_default_headers()
            return

        self.send_response(HTTPStatus.OK)
        self.set_default_headers()

        # DONT USE POSITIONAL ARGUMENTS, WILL NOT BE PASSED FORWARD.
        # This is just in case you want to add some variables on route_callback.
        # Aways use named parameters like below. Decorators handles just kwargs, not args.
        # If you wanna add a decorator, i thinks is better keep this pattern.
        data = route_callback(req=self, body=self.get_body())

        if isinstance(data, (dict, list)):
            data = json.dumps(data)

        self.wfile.write(data.encode("utf-8"))

    def do_GET(self) -> None:
        self.run_route(HTTPMethod.GET)

    def do_POST(self) -> None:
        self.run_route(HTTPMethod.POST)


def serve_api(ip: str, port: int) -> None:
    server = HTTPServer(((ip, port)), RequestHandler)

    print(f"Running api at: http://{ip}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
