from flask import Flask, redirect
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

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init("db/blogs.db")

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def main():
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).order_by(Posts.created_date.desc()).all()
    posts = [[elem.title, elem.author_id, elem.content] for elem in posts]
    return render_template('main.html', posts=posts)


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
    if form.validate_on_submit():
        db_sess = db_session.create_session()
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
            posts.append([elem.title, str(elem.created_date).split(' ')[0], elem.content])
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


@app.route('/user/<username>', methods=['GET'])
def find_user(username):
    db_sess = db_session.create_session()
    posts = []
    name = db_sess.query(User).filter(User.name == username).first().id
    for elem in db_sess.query(Posts).filter(Posts.author_id == name):
        posts.append([elem.title, str(elem.created_date).split(' ')[0], elem.content])
    try:
        if name == current_user.id:
            return render_template('my_page.html', posts=posts)
    except AttributeError:
        pass
    return render_template('user_page.html', name=username, posts=posts)


@app.route('/find', methods=['GET'])
def load_simply_questions(quantity=10):
    tasks = get_question(quantity)
    return render_template("get_question.html", questions=tasks)


@app.route('/find/<value>/<data>', methods=['GET'])
def find(value, data):
    tasks = get_question_with_params(20, value, data)
    return render_template("get_question.html", questions=tasks)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
