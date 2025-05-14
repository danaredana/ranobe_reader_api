from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class RanobeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    cover_image = StringField('Cover Image URL')
    submit = SubmitField('Submit')


class ChapterForm(FlaskForm):
    title = StringField('Название главы', validators=[DataRequired()])
    chapter_number = IntegerField('Номер главы', validators=[DataRequired()])
    content = TextAreaField('Содержание', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')


class VolumeForm(FlaskForm):
    title = StringField('Название тома', validators=[DataRequired()])
    volume_number = IntegerField('Номер тома', validators=[DataRequired()])
    description = TextAreaField('Описание тома')
    cover_image = StringField('Обложка тома (URL)')
    submit = SubmitField('Сохранить')
