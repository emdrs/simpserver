from http import HTTPMethod
from common import route

@route("/test", HTTPMethod.GET)
def get_role() -> dict:
    return { "Hello,": " World" }
