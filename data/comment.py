import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Comment(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'comments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    chapter_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("chapters.id"))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=sqlalchemy.func.now())

    user = orm.relationship('User')
    chapter = orm.relationship('Chapter', back_populates="comments")