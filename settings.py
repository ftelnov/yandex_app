UPLOAD_FOLDER = 'static/users_uploads'  # директория подгрузки изображений пользователей
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}  # доступные форматы подгрузки

SECRET_KEY = 'an1t2r42on335e'  # секретка приложения

DATABASE_URI = 'sqlite:///main_database.db'  # Uri бдшки
TRACK_MODIFICATIONS = DATABASE_URI  # отслеживание изменений

SESSION_TYPE = 'filesystem'  #

HOST = 'localhost'  # хост коннекта на сервер
PORT = 5000  # порт коннекта на сервер

# все коды месяцев и их строковые названия
MONTHS = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

STANDARD_IMAGE = 'static/img/user/1.jpg'  # стандартное изображение для профиля пользователя
ADMIN_PASSWORD = 'aethertemplarA1'  # пароль администратора


# функция построения запроса по локальному пути
def build_url(url):
    return 'http://' + HOST + ':' + str(PORT) + url