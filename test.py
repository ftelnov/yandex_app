import requests
from settings import build_url


def test_auth(login, password):
    result = requests.post(build_url('/api/auth'), data={'login': login, 'password': password})
    return result.text


def test_tasks(user_token):
    result = requests.get(build_url('/api/task'), params={'token': user_token}).json()
    return result


def test_edit_task(user_token, text, title, task_id):
    result = requests.put(build_url('/api/task/id'),
                          params={'token': user_token, 'text': text, 'title': title, 'task_id': task_id}).json()
    return result


def test_delete_task(user_token):
    result = requests.delete(build_url('/api/task/id'), params={'token': user_token}).json()
    return result


def test_get_task(user_token, task_id):
    result = requests.get(build_url('/api/task/id'), params={'token': user_token, 'task_id': task_id}).json()
    return result


def test_create_task(user_token, text, category, title):
    result = requests.post(build_url('/api/task'),
                           data={'token': user_token, 'text': text, 'category': category, 'title': title})
    return result.json()


def test_timer(user_token, task_id, timer, time):
    result = requests.post(build_url('/api/task/id/timer'),
                           data={'token': user_token, 'task_id': task_id, 'timer': timer, 'time': time})
    return result.json()


if __name__ == '__main__':
    print(test_tasks('1'))
