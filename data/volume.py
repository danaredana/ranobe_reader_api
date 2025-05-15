from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Volume(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'volumes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    volume_number = Column(Integer, nullable=False)
    ranobe_id = Column(Integer, ForeignKey('ranobe.id'))
    title = Column(String, nullable=True)

    ranobe = relationship('Ranobe', back_populates='volumes')
    chapters = relationship('Chapter', back_populates='volume', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Volume {self.volume_number}>'

    @property
    def display_title(self):
        return self.title if self.title else f"Том {self.volume_number}"
