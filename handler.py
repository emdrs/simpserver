from http import HTTPMethod, HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.parse
import traceback

from exceptions import APIError
from router import RouteCallbackReturn, route_get_callback
from routes import *  # Registering routes


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server) -> None:
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

        if not body_data: return {}

        body = json.loads(body_data)

        if not isinstance(body, dict): raise ValueError("Invalid body")

        return body

    def get_url_params(self) -> dict:
        if "?" not in self.path: return {}

        url_params = {}
        params_list = self.path.split("?")[1]

        params_list = params_list.split("&") if "&" in params_list else [params_list]

        for param in params_list:
            name, value = param.split("=")
            url_params[name] = urllib.parse.unquote_plus(value)

        return url_params

    def run_route(self, method: HTTPMethod) -> None:
        path = self.path
        if "?" in path:
            path = path.split("?")[0]

        route_callback = route_get_callback(path, method)

        if not route_callback:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.set_default_headers()
            return

        status_code = HTTPStatus.OK
        response: RouteCallbackReturn
        try:
            # DONT USE POSITIONAL ARGUMENTS, WILL NOT BE PASSED FORWARD.
            # This is just in case you want to add some variables on route_callback.
            # Aways use named parameters like below. Decorators handles just kwargs, not args.
            # If you want to create a decorator, i think that is better keep this pattern.
            response = route_callback(req=self,
                                      body=self.get_body(),
                                      url_params=self.get_url_params())
        except APIError as api_error:
            status_code = api_error.status_code
            response = api_error.response
        except:
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            print(traceback.format_exc())
            response = {"error": "Internal error"}

        self.send_response(status_code)
        self.set_default_headers()

        if isinstance(response, str):
            response = {"message": response}

        self.wfile.write(json.dumps(response).encode("utf-8"))

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
