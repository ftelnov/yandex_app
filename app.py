from flask import Flask, jsonify, render_template, request
from flask_restful import Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from settings import *
from secure import *
from requests import post

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


# класс задачи в базе данных
class Task(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)  # уникальный идентификатор задачи
    text = DB.Column(DB.Text)  # суть задачи
    user_id = DB.Column(DB.Integer)  # идентификатор создателя задачи


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        nickname = request.form.get('nickname')
        password = request.form.get('password')
        phone = request.form.get('number')
        account_type = 1 if request.form.get('superuser') else 0
        result = post(build_url('/api/users/register'),
                      data={'nickname': nickname, 'password': password, 'phone': phone, 'type': account_type})
        print(result.json())
        return render_template('signup.html')


# ------------------------- Api Methods -------------------------
@app.route('/api/get', methods=['POST'])
def users_get():
    parser = reqparse.RequestParser()
    parser.add_argument('id')
    result = parser.parse_args()
    if not result.id:
        return jsonify({'Error': 701})
    result = DB.session.query(User).filter_by(id=result.id).all()
    return jsonify(json_list=result)


@app.route('/api/reg', methods=['POST'])
def users_reg():
    parser = reqparse.RequestParser()
    parser.add_argument('login')
    parser.add_argument('password')
    result = parser.parse_args()
    if not result.login or not result.password:
        return jsonify({'Result': 'One of requirement parameters is missing!'})
    user = User(nickname=result.nickname, password=sha256(result.password),
                token=get_token(result.login, result.password), admin=False)
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
        result = parser.parse_args()
        if not result.token or not result.text:
            return jsonify({'Result': 'One of requirement parameters is missing!'})
        user = DB.session.query(User).filter_by(token=result.token).first()
        if not user:
            return jsonify({'Result': 'There are no such user!'})
        task = Task(text=result.text, user_id=user.id)
        try:
            DB.session.add(task)
            DB.session.commit()
        except Exception as exc:
            return jsonify({'Result': 'This task already exist!'})
        return jsonify({'Result': 'Added successfully'})


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


if __name__ == '__main__':
    DB.create_all()
    app.run(host=HOST, port=PORT, threaded=True)
