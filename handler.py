from http import HTTPMethod, HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.parse
import traceback
import signal
from datetime import datetime

from .exceptions import APIError
from .router import Route, RouteCallbackReturn, html, route, get_route_info
from .config import user_configs

def timeout_handler(signum, frame):
    raise TimeoutError()

signal.signal(signal.SIGALRM, timeout_handler)

class SimpleEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server) -> None:
        self.conn = None
        self.cur  = None
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
        signal.setitimer(signal.ITIMER_REAL, 0.01, 0)
        body_data = self.rfile.read(content_length).decode("utf-8")
        signal.setitimer(signal.ITIMER_REAL, 0)

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


    def get_path_params(self, route_info: Route) -> dict:
        if not route_info.path_params:
            return {}

        compatible_types = {"int": int, "str": str, "float": float}
        data_start_index = route_info.path.find(".*")

        return {
            param_name: compatible_types[param_type](self.path[data_start_index:])
            for param_name, param_type in route_info.path_params.items()
        }


    def run_route(self, method: HTTPMethod) -> None:
        path = self.path
        if "?" in path:
            path = path.split("?")[0]

        route_info = get_route_info(path, method)

        if not route_info:
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
            kwargs = {
                "req"       :self,
                "body"      :self.get_body(),
                "url_params":self.get_url_params()
            }

            if route_info.path_params:
                kwargs["path_params"] = self.get_path_params(route_info)

            response = route_info.callback(**kwargs)
        except APIError as api_error:
            status_code = api_error.status_code
            response = api_error.response
        except:
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            print(traceback.format_exc())
            response = {"error": "Internal error"}
        finally:
            """
            This solves a bug that if get an error with opened connection, the
            server freezes. Why? Because was not closed? I dont know.
            """
            if self.conn:
                self.cur.close()
                self.conn.close()



        self.send_response(status_code)
        self.set_default_headers()

        if isinstance(response, html):
            self.wfile.write(response.encode("utf-8"))
            return

        if isinstance(response, str):
            response = {"message": response}

        self.wfile.write(json.dumps(response,
                                    ensure_ascii=False,
                                    cls=SimpleEncoder).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.set_default_headers()

    def do_GET(self) -> None:
        self.run_route(HTTPMethod.GET)

    def do_PUT(self) -> None:
        self.run_route(HTTPMethod.PUT)

    def do_DELETE(self) -> None:
        self.run_route(HTTPMethod.DELETE)

    def do_POST(self) -> None:
        self.run_route(HTTPMethod.POST)


def serve_api(ip: str, port: int) -> None:
    server = HTTPServer(((ip, port)), RequestHandler)

    print(f"Running api at: http://{ip}:{port}")

    if user_configs["static_path"]:
        @route(f"{user_configs["static_url"]}<file:str>", HTTPMethod.GET)
        def serve_files(path_params: dict) -> str:
            return f"serving file: {path_params["file"]}"

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
