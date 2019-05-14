from flask import Flask, request
import logging
import json
import requests
import datetime

app = Flask(__name__)

# https://tech.yandex.ru/dialogs/alice/doc/sounds/music-docpage/

now = datetime.datetime.now()
logging.basicConfig(level=logging.INFO)

sessionStorage = {}
Buttons_list = [
    {
        'title': 'Да',
        'hide': True
    },
    {
        'title': 'Нет',
        'hide': True
    }
]

command_list = ['Просмотреть список задач', 'Просмотреть задачу ', 'Просмотреть список просроченных задач',
                'Добавить задачу', 'Делегировать задачу']
command_function_dict = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    team_name = ''
    if req['session']['new']:
        res['response'][
            'text'] = 'Добрый день, пожалуйста авторизуйтесь(сообщите логин и пароль) или зарегистрируйтесь(ФИО, логин, пароль)'
        sessionStorage[user_id] = {
            'state_of_dialogue': 1,  # 0 - задан вопрос, 1 - получен ответ
            'dialog_started': False,  # здесь информация о том, что пользователь начал игру. По умолчанию False
            'token': None

        }
        return
    if sessionStorage[user_id]['token'] is None:
        # Удостовеяемся, что пользователь ввёл корректные данные
        control_correct_user(req, res, user_id)
    else:
        for text, func in zip(command_list, [get_all_task(req, user_id), get_task(req, user_id, True),
                                             get_old_task(req, user_id), nosutit_task(req, get_user_FIO(req, user_id,
                                                                                                        sessionStorage[
                                                                                                            user_id][
                                                                                                            'token']),
                                                                                      user_id),
                                             insert_task(req)]):
            command_function_dict[text] = func
        res['response']['text'] = command_function_dict[
            list(filter(lambda x: x.lower() in req['request']['command'], command_list))[0]]


def control_correct_user(req, res, user_id):
    command = req['request']['command'].split()
    if len(command) == 2:
        # проверка на существование пользователя
        sessionStorage[user_id]['token'] = requests.get('https://pydocs.ru:5000/yandex/api/auth',
                                                        params={'login': command[0], 'password': command[1]}).json()
        if sessionStorage[user_id]['token'] == 'There are no such user!':
            res['response'][
                'text'] = 'Такого пользователя не существует. Возможно вы ввели неверные данные, или ваш аккаунт был удалён админом.Попробуйте войти ещё раз'
            return False
        else:
            sessionStorage[user_id]['token'] = sessionStorage[user_id]['token']['token']
            res['response']['text'] = 'Здравствуйте ' + get_user_FIO(req, user_id, sessionStorage[user_id]['token'])[
                0] + '. Вы можете: \n' + '\n'.join(
                command_list) + 'Формат при добавлении задачи : Добавить задачу <заголовок задачи> текст задачи <текст задачи> категория <тег> дедлайн <крайнее время выполнения>. Формат при делегированизадачи: Делегировать задачу <заголовок задачи> коллеге <ФИО коллеги> '
            sessionStorage[user_id]['user_name'] = command[0]
            return True

    if len(command) == 5:
        requests.post('https://pydocs.ru:5000/yandex/api/reg',
                      params={'first': command[0], 'second': command[1], 'third': command[2],
                              'login': command[3], 'password': command[4]})
        # занесение в бд
        res['response']['text'] = 'Здравствуйте ' + command[0] + '. Вы можете: \n' + '\n'.join(
            command_list)
        sessionStorage[user_id]['user_name'] = command[3]
        return True


def get_user_FIO(req, user_id, token=None):
    for i in get_all_task(req, user_id):
        if i['token'] == token:
            return (i['first'], i['second'], i['third'])


def get_all_task(req, user_id, str_=False):
    if str_:
        return '\n -'.join(map(lambda x: x['title'], requests.get('https://pydocs.ru:5000/yandex/api/task', params={
            'token': sessionStorage[user_id]['token']}).json()))
    else:
        return requests.get('https://pydocs.ru:5000/yandex/api/task',
                            params={'token': sessionStorage[user_id]['token']}).json()


def get_task(res, req, user_id):
    return requests.get('https://pydocs.ru:5000/yandex/api/task/id', params={
        'id': find_id_about_title(req, make_text(req['request']['command'], [command_list[1]]),
                                  user_id)}).json().first()[
        'title']


def get_old_task(req, user_id):
    return '\n -'.join(map(lambda x: x['title'], filter(lambda x: x['active'] == False, get_all_task(req, user_id))))


# Добавить задачу <заголовок задачи> текст задачи <текст задачи> категория <тег> дедлайн <крайнее время выполнения>.
# Формат при делегированизадачи: Делегировать задачу <заголовок задачи> коллеге <ФИО коллеги> '
def insert_task(req):
    text = make_text(req['request']['command'], ['Добавить задачу', 'текст задачи', 'категория', 'дедлайн'])
    requests.post('https://pydocs.ru:5000/yandex/api/task',
                  params={'text': text[1], 'title': text[0], 'category': text[2], 'dedline': silect_time(text[3])})
    return 'Задача добавлена'


def nosutit_task(req, FIO, user_id):
    new_user = list(filter(lambda i: (i['first'], i['second'], i['third']), get_all_task(req, user_id)))
    new_user = new_user[0] if len(new_user) > 1 else False
    if new_user:
        # requests.post('https://pydocs.ru:5000/yandex/api/task/id', params={'user_id':}
        text = make_text(req['request']['command'], ['Делегировать задачу', 'коллеге'])
        return 'Задача делегирована'
    else:
        return 'Введены некорректные данные'


def make_text(text, li):
    for i in li:
        text = '~'.join(text.split(i))
    return text.split('~')[1:]


def find_id_about_title(req, title, user_id):
    for i in get_all_task(req, user_id):
        if i['title'] == title:
            return i['id']


def silect_time(str_time):
    week_di = {'следующий': 7, 'понедельник': 1, 'вторник': 2, 'среда': 3, 'четверг': 4, 'пятница': 5, 'суббота': 6,
               'воскресенье': 7}
    di = {'завтра': 1, 'послезавтра': 2, 'следующий': 7, 'понедельник': 1, 'вторник': 2, 'среда': 3, 'четверг': 4,
          'пятница': 5, 'суббота': 6, 'воскресенье': 7}
    plas = sum(list(map(lambda x: di[x], str_time.split()[0].split)))
    if any(list(map(lambda x: x in week_di, str_time.split()))):
        plas -= di[datetime.datetime.today().strftime("%A")]
    return plas * 3600