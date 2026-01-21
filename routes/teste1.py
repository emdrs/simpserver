from http import HTTPMethod

from router import route


@route("/teste1", HTTPMethod.GET)
def test() -> dict:
    return {"Mista": "Azozin"}
