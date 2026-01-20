from http.server import BaseHTTPRequestHandler
from http import HTTPMethod, HTTPStatus
import json
import importlib
from socketserver import BaseServer
from exceptions import APIError
import traceback
from urllib.parse import unquote_plus


class RequestHandler(BaseHTTPRequestHandler):
    routes = {}

    @classmethod
    def initialize(cls):
        methods = (
            HTTPMethod.GET,
            HTTPMethod.POST,
            HTTPMethod.PUT,
            HTTPMethod.DELETE,
        )

        import routes

        modules_names = [name for name in dir(routes) if not name.startswith("__")]
        functions = [
            f
            for module_name in modules_names
            for f in importlib.import_module(f"routes.{module_name}").__dict__.values()
            if hasattr(f, "api")
        ]

        cls.routes = {
            m: {
                attr[0]: f
                for f in functions
                if (attr := getattr(f, "api")) and attr[1] == m
            }
            for m in methods
        }
        print(cls.routes)

    def __init__(self, request, client_address, server: BaseServer) -> None:
        self.response_sent = False
        super().__init__(request, client_address, server)

    def set_headers(
        self,
        status: HTTPStatus,
        message: str | None = None,
        data: dict | list | None = None,
    ):
        if self.response_sent:
            return

        self.send_response(status, message)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "token, Content-Type")
        if data:
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            if isinstance(data, dict):
                from common import ModelData

                for k, v in data.items():
                    if isinstance(v, ModelData):
                        data[k] = v.dict()
            # elif isinstance(data, list):
            # data = [item.dict() for item in data]

            print(data)

            self.wfile.write(json.dumps(data).encode("utf8"))
        else:
            self.end_headers()
        self.response_sent = True

    def run_routes(self, method: HTTPMethod):
        self.response_sent = False
        for path, func in RequestHandler.routes[method].items():
            if path == (
                self.path if "?" not in self.path else self.path[: self.path.index("?")]
            ):
                try:
                    params = {}
                    if "?" in self.path:
                        string_params = self.path.split("?")[1]
                        splitted_string_params = (
                            string_params.split("&")
                            if "&" in string_params
                            else [string_params] if string_params else []
                        )

                        for param in splitted_string_params:
                            p, v = param.split("=")
                            params[unquote_plus(p)] = unquote_plus(v)

                    from common import safe_run

                    return safe_run(func, (self,), {"params": params})
                except ValueError as ve:
                    print(traceback.format_exc(), flush=True)
                    print(str(ve), flush=True)
                    self.set_headers(HTTPStatus.BAD_REQUEST, data={"error": str(ve)})
                except BrokenPipeError:
                    print("Client disconnected before get response.", flush=True)
                except APIError as e:
                    print(traceback.format_exc(), flush=True)
                    self.set_headers(e.status_code, data={"error": e.msg})
                except Exception as e:
                    print(traceback.format_exc(), flush=True)
                    print(f"Unexpected error: {e}", flush=True)
                    self.set_headers(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        data={"error": "Internal server error"},
                    )
                return
        self.set_headers(HTTPStatus.NOT_FOUND)

    def do_OPTIONS(self):
        self.set_headers(HTTPStatus.NO_CONTENT)

    def do_GET(self):
        self.set_headers(HTTPStatus.OK, data=self.run_routes(HTTPMethod.GET))

    def do_POST(self):
        self.set_headers(HTTPStatus.CREATED, data=self.run_routes(HTTPMethod.POST))

    def do_PUT(self):
        self.set_headers(HTTPStatus.NO_CONTENT, data=self.run_routes(HTTPMethod.PUT))

    def do_DELETE(self):
        self.set_headers(HTTPStatus.NO_CONTENT, data=self.run_routes(HTTPMethod.DELETE))
