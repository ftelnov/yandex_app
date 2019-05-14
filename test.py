import requests
from settings import build_url


def test_auth(login, password):
    result = requests.post(build_url('/api/auth'), data={'login': login, 'password': password}).json()
    return result
