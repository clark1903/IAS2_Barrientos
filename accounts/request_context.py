from threading import local


_state = local()


def set_request_context(user=None, ip_address=""):
    _state.user = user
    _state.ip_address = ip_address


def clear_request_context():
    _state.user = None
    _state.ip_address = ""


def get_current_user():
    return getattr(_state, "user", None)


def get_current_ip():
    return getattr(_state, "ip_address", "")
