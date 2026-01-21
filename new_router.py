from http import HTTPMethod
from typing import Callable

routes: dict[HTTPMethod, dict[str, Callable]] = {
    HTTPMethod.GET: {},
    HTTPMethod.POST: {},
    HTTPMethod.PUT: {},
    HTTPMethod.DELETE: {},
}
