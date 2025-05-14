import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase

class Ranobe(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'ranobe'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    cover_image = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=sqlalchemy.func.now())

    # Отношения
    author = orm.relationship('User')
    volumes = orm.relationship('Volume', back_populates='ranobe', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Ranobe {self.id} {self.title}>'