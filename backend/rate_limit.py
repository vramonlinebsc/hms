import time
from flask import request, jsonify

WINDOW_SECONDS = 60
MAX_REQUESTS = 60  # per IP per endpoint


_request_log = {}


def rate_limiter():
    key = f"{request.remote_addr}:{request.endpoint}"
    now = time.time()

    window_start = now - WINDOW_SECONDS
    timestamps = _request_log.get(key, [])

    # prune old requests
    timestamps = [ts for ts in timestamps if ts > window_start]

    if len(timestamps) >= MAX_REQUESTS:
        return jsonify(error="Rate limit exceeded"), 429

    timestamps.append(now)
    _request_log[key] = timestamps
