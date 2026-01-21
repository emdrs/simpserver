from http import HTTPMethod

from router import route


@route("/teste2", HTTPMethod.GET)
def test() -> list:
    return ["Mista", "Azozin"]
