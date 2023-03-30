import json

import schedule
from flask import Flask, redirect, request
from flask import render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import EmailField, PasswordField, IntegerField, SubmitField, StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired

from data import db_session
from data.posts import Posts
from data.user import User
from generate_questions import get_question, get_question_with_params


def update_info():
    data = {}
    for i in range(1, 11):
        data[i] = get_question_with_params(1, i * 100)
    with open('static/day.json', 'w') as outfile:
        json.dump(data, outfile)


schedule.every().day.at("00:00").do(update_info)
schedule.run_pending()
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init("db/blogs.db")
MAX_CONTENT_LENGTH = 1024 * 1024 * 5
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


class Search_Form(FlaskForm):
    find_id = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Поиск')


def search(data):
    db_sess = db_session.create_session()
    if data.isdigit():
        if int(data) == current_user.id:
            return '/me'
        if int(data) <= db_sess.query(User).order_by(User.id.desc()).first().id:
            return f'/user/{data}'
        if int(data) <= db_sess.query(Posts).order_by(Posts.id.desc()).first().id:
            uid = db_sess.query(Posts).filter(Posts.id == data).first().author_id
            tex = db_sess.query(User).filter(User.id == uid).first().id
            return f'/user/{tex}'
    else:
        try:
            tex = db_sess.query(User).where(User.name.like(f'%{data.lower()}%')).first().id
            return f'/user/{tex}'
        except Exception as e:
            return '/'


@app.route('/', methods=['GET', 'POST'])
def main():
    form = Search_Form()
    db_sess = db_session.create_session()
    tex = db_sess.query(Posts).order_by(Posts.created_date.desc()).all()
    posts = []
    for elem in tex:
        tmp = db_sess.query(User).filter(User.id == elem.author_id).first().name
        posts.append([elem.title, tmp, elem.content, elem.author_id])
    if form.validate_on_submit():
        a = search(form.find_id.data)
        return redirect(a)
    return render_template('main.html', posts=posts, form=form)


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    age = IntegerField('Возраст', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        if form.age.data < 3:
            return render_template('register.html', form=form, message='You are too young')
        if db_sess.query(User).filter(User.email == form.email.data).all():
            return render_template('register.html', form=form, message='This e-mail was already used')
        user = User()
        user.email = form.email.data
        user.age = form.age.data
        user.surname = form.surname.data
        user.name = form.name.data
        user.check_password = generate_password_hash(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', form=form)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and check_password_hash(user.check_password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_required
@app.route('/me', methods=['GET', 'POST'])
def load_my_page():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        posts = []
        for elem in db_sess.query(Posts).filter(Posts.author_id == current_user.id):
            posts.append([elem.title, str(elem.created_date).split(' ')[0], elem.content, elem.id])
        return render_template('my_page.html', posts=posts)
    else:
        return redirect('/register')


class AddpostForm(FlaskForm):
    title = StringField('Название викторины', validators=[DataRequired()])
    content = TextAreaField('Содержание', validators=[DataRequired()])

    submit = SubmitField('Опубликовать')


@app.route('/addpost', methods=['GET', 'POST'])
def add_post():
    if current_user.is_authenticated:
        form = AddpostForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            post = Posts()
            post.author_id = current_user.id
            post.title = form.title.data
            post.content = form.content.data
            db_sess.add(post)
            db_sess.commit()
            return redirect("/me")
        return render_template('add_post.html', title='Авторизация', question=get_question(1), form=form)
    else:
        return render_template('dont_hack.html')


@app.route('/user/<id>', methods=['GET'])
def find_user(id):
    db_sess = db_session.create_session()
    try:
        username = db_sess.query(User).filter(User.id == id).first().name
        posts = []
        for elem in db_sess.query(Posts).filter(Posts.author_id == id):
            posts.append([elem.title, str(elem.created_date).split(' ')[0], elem.content])
        try:
            if id == current_user.id:
                return render_template('my_page.html', posts=posts)
        except AttributeError:
            pass
        return render_template('user_page.html', name=username, posts=posts, id=id)
    except Exception as e:
        return "Something get wrong, please return to the previous page. Thanks"


@app.route('/find', methods=['GET'])
def load_simply_questions(quantity=10):
    tasks = get_question(quantity)
    return render_template("get_question.html", questions=tasks)


@app.route('/find/<value>', methods=['GET'])
def find(value):
    tasks = get_question_with_params(20, value)
    return render_template("get_question.html", questions=tasks)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        file.save(f'static/avatar/{current_user.id}.jpg')
        return redirect('/me')
    return render_template('upload.html')


@app.route('/delete_post/<post_id>', methods=['GET', 'POST'])
def delete_post(post_id):
    db_sess = db_session.create_session()
    post = db_sess.query(Posts).get(post_id)
    db_sess.delete(post)
    db_sess.commit()
    return redirect('/me')


@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    res = []
    for i in range(100, 1100, 100):
        tex = get_question_with_params(10, i)
        tex.append(i)
        res.append(tex)
    return render_template('create_quiz.html', posts=res)


class DailyForm(FlaskForm):
    with open('static/day.json', 'r') as f:
        info = json.load(f)
    q_1 = StringField(f'{info["1"][0][0]}', validators=[DataRequired()])
    q_2 = StringField(f'{info["2"][0][0]}', validators=[DataRequired()])
    q_3 = StringField(f'{info["3"][0][0]}', validators=[DataRequired()])
    q_4 = StringField(f'{info["4"][0][0]}', validators=[DataRequired()])
    q_5 = StringField(f'{info["5"][0][0]}', validators=[DataRequired()])
    q_6 = StringField(f'{info["6"][0][0]}', validators=[DataRequired()])
    q_7 = StringField(f'{info["7"][0][0]}', validators=[DataRequired()])
    q_8 = StringField(f'{info["8"][0][0]}', validators=[DataRequired()])
    q_9 = StringField(f'{info["9"][0][0]}', validators=[DataRequired()])
    q_10 = StringField(f'{info["10"][0][0]}', validators=[DataRequired()])
    submit = SubmitField('Отправить на проверку')

def check(num, ans):
    with open('static/day.json', 'r') as f:
        info = json.load(f)
        return info[num][0][1].lower().strip() == ans.lower().strip()


@app.route('/daily', methods=['GET', 'POST'])
def daily():
    if current_user.is_authenticated():
        form = DailyForm()
        res = 0
        if form.validate_on_submit():
            if check('1', form.q_1.data):
                res += 100
            if check('2', form.q_2.data):
                res += 200
            if check('3', form.q_3.data):
                res += 300
            if check('4', form.q_4.data):
                res += 400
            if check('5', form.q_5.data):
                res += 500
            if check('6', form.q_6.data):
                res += 600
            if check('7', form.q_7.data):
                res += 700
            if check('8', form.q_8.data):
                res += 800
            if check('9', form.q_9.data):
                res += 900
            if check('10', form.q_10.data):
                res += 1000
            db_sess = db_session.create_session()
            Usr = db_sess.query(User).filter(User.id == current_user.id).first()
            if Usr.rating:
                Usr.rating += res
            else:
                Usr.rating = res
            db_sess.commit()
            return redirect('/')
        return render_template('daily.html', form=form)
    return render_template('dont_hack.html')




if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
while True:
    schedule.run_pending()
