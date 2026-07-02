from django.http import HttpRequest

from rest_framework.request import Request


def get_ip_from_request(request: HttpRequest | Request) -> str | None:
    """Return the client's IP from the X-Forwarded-For chain.

    This trusts the FIRST entry of ``X-Forwarded-For``, so it is ONLY correct behind a
    trusted reverse proxy.

    REQUIREMENT: the outermost (edge) reverse proxy MUST set the real client address as
    the first ``X-Forwarded-For`` hop and MUST NOT trust a client-supplied value —
    otherwise a client can spoof its IP by sending its own ``X-Forwarded-For`` header.
    Each subsequent proxy must only *append* (never reorder), so the first entry stays
    the original client. With such an edge in place the value is authoritative; without
    one, do NOT trust this header (fall back to ``REMOTE_ADDR``).

    Note: the in-stack nginx here appends via ``$proxy_add_x_forwarded_for``, so the
    guarantee rests on the EDGE proxy in front of it doing the above correctly.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
