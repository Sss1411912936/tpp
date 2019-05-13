import uuid

ADMIN = 'admin'
CINEMA = 'cinema'
VIEWER = 'viewer'


def generrate_token(prefix):
    token = uuid.uuid4().hex

    return prefix + token


def generrate_admin_token():
    return generrate_token(ADMIN)


def generrate_cinema_token():
    return generrate_token(CINEMA)


def generrate_viewer_token():
    return generrate_token(VIEWER)
