from http import HTTPMethod

from router import route


@route("/teste2", HTTPMethod.GET)
def test() -> str:
    return "World"
