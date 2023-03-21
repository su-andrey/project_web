import sqlalchemy
import flask_login
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, flask_login.UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    age = sqlalchemy.Column(sqlalchemy.Integer)
    email = sqlalchemy.Column(sqlalchemy.String)
    check_password = sqlalchemy.Column(sqlalchemy.String)