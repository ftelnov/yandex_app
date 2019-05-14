from flask import Flask, jsonify, render_template, request, session, redirect
from flask_restful import Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from settings import *
from secure import *
from requests import post, get
from datetime import datetime, timedelta

app = Flask(__name__)
# настраиваем конфиги
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI  # ссылка на бд
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # отслеживание изменений
app.config['SESSION_TYPE'] = SESSION_TYPE  # тип для сеанса
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # директория подгрузки пользовательских изображений
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # максимальная длительность жизни файлов на сервере( для обновления )
Api(app)  # инициализируем API к приложению

# устанавливаем секретку
app.secret_key = SECRET_KEY

# главная база данных
DB = SQLAlchemy(app)


# models
# класс пользователя в базе данных
class User(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)  # уникальный идентификатор пользователя
    login = DB.Column(DB.String(120), unique=True, nullable=False)  # имя пользователя
    password = DB.Column(DB.String(120), unique=False, nullable=False)  # пароль пользователя
    token = DB.Column(DB.String, unique=True, nullable=False)  # токен пользователя
    admin = DB.Column(DB.Boolean)  # флаг аккаунта
    first_name = DB.Column(DB.String)  # имя
    second_name = DB.Column(DB.String)  # фамилия
    third_name = DB.Column(DB.String)  # отчетво


# класс задачи в базе данных
class Task(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)  # уникальный идентификатор задачи
    title = DB.Column(DB.String)  # заголовок задачи
    text = DB.Column(DB.Text)  # суть задачи
    user_id = DB.Column(DB.Integer)  # идентификатор создателя задачи
    alive = DB.Column(DB.Integer, default=1)  # жива ли задача


# класс категории в базе данных
class Category(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)  # уникальный идентификатор категории
    peer_id = DB.Column(DB.Integer)  # назначение категории
    title = DB.Column(DB.String)  # заголовок категории


class Timer(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)  # уникальный идентификатор таймера
    task_id = DB.Column(DB.Integer)  # айди задачи
    time_start = DB.Column(DB.Date)  # время старта
    time_end = DB.Column(DB.Date)  # время окончания
    alive = DB.Column(DB.Integer, default=1)  # живой ли таймер


class Comment(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)  # уникальный идентификатор комментария
    peer_id = DB.Column(DB.Integer)
    text = DB.Column(DB.String)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('token'):
        return redirect('/login')
    user = DB.session.query(User).filter_by(token=session.get('token')).first()
    if request.method == 'GET':
        return render_template('profile.html', nickname=user.login, token=user.token)
    elif request.method == 'POST':
        if request.form.get('sign-out'):
            session['token'] = ''
        if request.form.get('delete-account'):
            DB.session.delete(user)
            DB.session.commit()
            session['token'] = ''
        return redirect('/login')


@app.route('/register', methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        if session.get('token'):
            return redirect('/profile')
        return render_template('signup.html')
    elif request.method == 'POST':
        nickname = request.form.get('nickname')
        password = request.form.get('password')
        password_confirm = request.form.get('password_submit')
        first = request.form.get('first_name')
        second = request.form.get('second_name')
        third = request.form.get('third_name')
        if password != password_confirm:
            return render_template('signup.html')
        result = post(build_url('/api/reg'),
                      data={'login': nickname, 'password': password, 'first': first, 'second': second,
                            'third': third}).json()
        if result.get('token'):
            session['token'] = result.get('token')
            return redirect('/profile')
        alert = '''<div class="alert alert-danger text-left mt-md-2 pd-1" role="alert">
                            {res}
                            </div>'''.format(res=result['Result'])
        return render_template('signup.html', response=alert)


@app.route('/login', methods=['POST', 'GET'])
def signin():
    if request.method == 'GET':
        if session.get('token'):
            return redirect('/profile')
        return render_template('signin.html')
    elif request.method == 'POST':
        nickname = request.form.get('nickname')
        password = request.form.get('password')
        result = post(build_url('/api/auth'),
                      data={'login': nickname, 'password': sha256(password)}).json()
        if result.get('token'):
            session['token'] = result.get('token')
            return redirect('/profile')
        alert = '''<div class="alert alert-danger text-left mt-md-2 pd-1" role="alert">
                            {res}
                            </div>'''.format(res=result['Result'])
        return render_template('signin.html', response=alert)


@app.route('/tasks', methods=['GET'])
def tasks():
    token = session.get('token')
    if not token:
        return redirect('/signin')
    result = get(build_url('/api/task'), params={'token': token}).json()
    if result.get('json_list'):
        return render_template('tasks.html', tasks=result['json_list'])
    return render_template('tasks.html')


@app.route('/add-task', methods=['GET', 'POST'])
def add_task():
    token = session.get('token')
    if not token:
        return redirect('/signin')
    if request.method == 'GET':
        return render_template('write-task.html')
    else:
        title = request.form.get('title')
        text = request.form.get('text')
        time = request.form.get('time')
        category = request.form.get('category')
        result = post(build_url('/api/task'), data={'token': token, 'title': title, 'text': text, 'Category': category}).json()
        result_2 = post(build_url('/api/task/id/timer'),
                        data={'token': token, 'time': time, 'timer': 1, 'task_id': result['Id']}).json()
        return redirect('/tasks')


# обработчик 404-ошибки
@app.errorhandler(404)
def error_404(error):
    return render_template('not-found.html')


# дефолтная страница
@app.route('/', methods=['GET'])
def default():
    return redirect('/start')


# стартовая страничка
@app.route('/start', methods=['GET'])
def index():
    return render_template('index.html')


# ------------------------- Api Methods -------------------------
@app.route('/api/title/set', methods=['POST'])
def title_set():
    parser = reqparse.RequestParser()
    parser.add_argument('token')
    parser.add_argument('task_id')
    parser.add_argument('title')
    result = parser.parse_args()
    if not result.token or not result.task_id or not result.title:
        return jsonify({'Result': 'One of requirement parameters is missing!'})
    user = DB.session.query(User).filter_by(token=result.token).first()
    if not user:
        return jsonify({'Result': 'Such user does not exist!'})
    task = DB.session.query(Task).filter_by(user_id=user.id, id=int(result.task_id)).first()
    if not task:
        return jsonify({'Result': 'There are no such tasks!'})
    task.title = result.title
    DB.session.commit()
    return jsonify({'Result': 'Successfully done!'})


@app.route('/api/title/get', methods=['GET'])
def title_get():
    token = request.args.get('token')
    title = request.args.get('title')
    task_id = request.args.get('task_id')
    if not token or not task_id or not title:
        return jsonify({'Result': 'One of requirement parameters is missing!'})
    user = DB.session.query(User).filter_by(token=token).first()
    if not user:
        return jsonify({'Result': 'Such user does not exist!'})
    task = DB.session.query(Task).filter_by(user_id=user.id, id=int(task_id)).first()
    if not task:
        return jsonify({'Result': 'There are no such tasks!'})
    return jsonify({'Result': 'Successfully done!', 'Title': task.title})


@app.route('/api/reg', methods=['POST'])
def users_reg():
    parser = reqparse.RequestParser()
    parser.add_argument('login')
    parser.add_argument('password')
    parser.add_argument('first')
    parser.add_argument('second')
    parser.add_argument('third')
    result = parser.parse_args()
    if not result.login or not result.password:
        return jsonify({'Result': 'One of requirement parameters is missing!'})
    user = User(login=result.login, password=sha256(result.password),
                token=get_token(result.login, result.password), admin=False, first_name=result.first,
                second_name=result.second, third_name=result.third)
    try:
        DB.session.add(user)
        DB.session.commit()
    except Exception as exc:
        return jsonify({'Result': 'User already exist!'})
    return jsonify({'Result': 'User successfully created!', 'token': user.token})


@app.route('/api/auth', methods=['POST'])
def users_auth():
    parser = reqparse.RequestParser()
    parser.add_argument('login')
    parser.add_argument('password')
    result = parser.parse_args()
    if not result.login or not result.password:
        return jsonify({'Result': 'One of requirement parameters is missing!'})
    user = DB.session.query(User).filter_by(login=result.login, password=result.password).first()
    if not user:
        return jsonify({'Result': 'There are no such user!'})
    return jsonify({'Result': 'Auth successfully', 'token': user.token})


@app.route('/api/task', methods=['GET', 'POST'])
def get_all_tasks():
    if request.method == 'GET':
        token = request.args.get('token')
        if not token:
            return jsonify({'Result': 'One of requirement parameters is missing!'})
        user = DB.session.query(User).filter_by(token=token).first()
        if not user:
            return jsonify({'Result': 'Such user does not exist!'})
        tasks = DB.session.query(Task).filter_by(user_id=user.id).all()
        return jsonify(json_list=tasks)

    elif request.method == 'POST':
        parser = reqparse.RequestParser()
        parser.add_argument('token')
        parser.add_argument('text')
        parser.add_argument('category')
        parser.add_argument('title')
        result = parser.parse_args()
        if not result.token:
            return jsonify({'Result': 'Token param is missing!'})
        if not result.text:
            return jsonify({'Result': 'Text param is missing!'})
        user = DB.session.query(User).filter_by(token=result.token).first()
        if not user:
            return jsonify({'Result': 'There are no such user!'})
        task = Task(text=result.text, user_id=user.id, title=result.title)
        try:
            DB.session.add(task)
            DB.session.commit()
        except Exception as exc:
            return jsonify({'Result': 'This task already exist!'})
        if result.category:
            category = Category(peer_id=task.id, title=result.category)
            DB.session.add(category)
            DB.session.commit()
        return jsonify({'Result': 'Added successfully', 'Id': task.id})


@app.route('/api/task/id', methods=['GET', 'PUT', 'DELETE'])
def get_task():
    if request.method == 'GET':
        task_id = request.args.get('id')
        token = request.args.get('token')
        if not token or not task_id:
            return jsonify({'Result': 'One of requirement parameters is missing!'})
        user = DB.session.query(User).filter_by(token=token).first()
        if not user:
            return jsonify({'Result': 'Such user does not exist!'})
        task = DB.session.query(Task).filter_by(user_id=user.id, id=int(task_id)).all()
        return jsonify(json_list=task)

    elif request.method == 'PUT':
        task_id = request.args.get('id')
        token = request.args.get('token')
        text = request.args.get('text')
        if not token or not task_id or not text:
            return jsonify({'Result': 'One of requirement parameters is missing!'})
        user = DB.session.query(User).filter_by(token=token).first()
        if not user:
            return jsonify({'Result': 'Such user does not exist!'})
        task = DB.session.query(Task).filter_by(user_id=user.id, id=int(task_id)).first()
        if not task:
            return jsonify({'Result': 'There are no such task!'})
        task.text = text
        DB.session.commit()
        return jsonify({'Result': 'Successfully!'})

    elif request.method == 'DELETE':
        task_id = request.args.get('id')
        token = request.args.get('token')
        if not task_id or not token:
            return jsonify({'Result': 'One of requirement parameters is missing!'})
        user = DB.session.query(User).filter_by(token=token).first()
        if not user:
            return jsonify({'Result': 'Such user does not exist!'})
        task = DB.session.query(Task).filter_by(user_id=user.id, id=int(task_id)).first()
        if not task:
            return jsonify({'Result': 'There are no such task!'})
        DB.session.delete(task)
        return jsonify({'Result': 'Task successfully deleted!'})


@app.route('/api/task/id/timer', methods=['POST'])
def timer():
    token = request.args.get('token')
    task_id = request.args.get('task_id')
    flag = request.args.get('timer')
    time = request.args.get('time')
    if not task_id or not token or not time:
        return jsonify({'Result': 'One of requirement parameters is missing!'})
    user = DB.session.query(User).filter_by(token=token).first()
    if not user:
        return jsonify({'Result': 'Such user does not exist!'})
    task = DB.session.query(Task).filter_by(user_id=user.id, id=int(task_id)).first()
    if not task:
        return jsonify({'Result': 'There are no such task!'})
    if flag:
        refl = DB.session.query.filter_by(task_id=task_id).first()
        now = datetime.now()
        end = now + timedelta(minutes=time)
        if not refl:
            new_timer = Timer(task_id=task_id, time_start=now, time_end=end)
            DB.session.add(new_timer)
        else:
            refl.time_start = now
            refl.time_end = end
        DB.session.commit()
    else:
        refl = DB.session.query.filter_by(task_id=task_id).first()
        refl.alive = False
        DB.session.commit()
    return jsonify({'Result': 'Successfully proceeded!'})


if __name__ == '__main__':
    DB.create_all()
    app.run(host=HOST, port=PORT, threaded=True)
