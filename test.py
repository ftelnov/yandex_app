import requests
from settings import build_url


def test_auth(login, password):
    result = requests.post(build_url('/api/auth'), data={'login': login, 'password': password})
    return result.text


def test_tasks(user_token):
    result = requests.get(build_url('/api/task'), params={'token': user_token}).json()
    return result


if __name__ == '__main__':
    print(test_tasks('1'))
