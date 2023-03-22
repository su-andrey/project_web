from flask import Flask, redirect
from flask import render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import EmailField, PasswordField, IntegerField, SubmitField, StringField, BooleanField, FieldList
from wtforms.validators import DataRequired
from data.posts import Posts
from data import db_session
from data.user import User
from generate_questions import get_question

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
    quest = get_question(10)
    return render_template('main.html', questions=quest)


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
        return render_template('my_page.html')
    else:
        return redirect('/register')


class AddpostForm(FlaskForm):
    title = StringField('Название викторины', validators=[DataRequired()])
    content = StringField('Содержание', validators=[DataRequired()])
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
        return render_template('add_post.html', title='Авторизация', form=form)
    else:
        return render_template('dont_hack.html')


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
