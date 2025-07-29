from typing import Optional, Union

from django.http import HttpRequest
from rest_framework.request import Request


def get_ip_from_request(request: Union[HttpRequest, Request]) -> Optional[str]:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0]
    else:
        ip_address = request.META.get("REMOTE_ADDR")
    return ip_address
