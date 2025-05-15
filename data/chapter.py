import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Chapter(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'chapters'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    chapter_number = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    volume_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('volumes.id'))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=sqlalchemy.func.now())

    volume = orm.relationship('Volume', back_populates='chapters')
    comments = orm.relationship('Comment', back_populates='chapter', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Chapter {self.id} {self.title}>'
