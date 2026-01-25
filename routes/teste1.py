from http import HTTPMethod

from router import RouteCallbackReturn, route


@route("/teste1", HTTPMethod.GET)
def test(url_params: dict) -> RouteCallbackReturn:
    return f"get oarams: {url_params}"
