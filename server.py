import os

from flask import Flask, render_template, redirect, request, abort, flash, jsonify, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime

from werkzeug.utils import secure_filename

from forms.user import RegisterForm, LoginForm
from forms.ranobe import RanobeForm, ChapterForm, CommentForm
from data.users import User
from data.ranobe import Ranobe
from data.volume import Volume
from data.chapter import Chapter
from data.comment import Comment
from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


# загрузка пользователя
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    try:
        return db_sess.query(User).get(user_id)
    finally:
        db_sess.close()


# главная страница
@app.route('/')
def index():
    db_sess = db_session.create_session()
    try:
        ranobe_list = db_sess.query(Ranobe).order_by(Ranobe.title).all()
        return render_template('index.html', ranobe_list=ranobe_list)
    finally:
        db_sess.close()


# регистрация нового пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', form=form)

            avatar_filename = 'default.jpg'

            # если загружен пользовательский аватар
            if form.avatar.data:
                avatar = form.avatar.data
                avatar_filename = f"user_{datetime.now().timestamp()}.{secure_filename(avatar.filename).split('.')[-1]}"
                avatar.save(os.path.join('static', 'uploads', 'avatars', avatar_filename))

            user = User(
                username=form.username.data,
                email=form.email.data,
                avatar=avatar_filename,
                created_date=datetime.now()
            )
            user.set_password(form.password.data)

            db_sess.add(user)
            db_sess.commit()

            login_user(user)
            return redirect(url_for('index'))

        except Exception as e:
            db_sess.rollback()
            app.logger.error(f"Registration error: {e}")
        finally:
            db_sess.close()

    return render_template('register.html', form=form)


# вход в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            user = db_sess.query(User).filter(User.email == form.email.data).first()

            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page or '/')

            flash('Неправильный логин или пароль', 'danger')
        finally:
            db_sess.close()
    return render_template('login.html', form=form)


# выход (по нажатию на никнейм)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


# страница определенного ранобе
@app.route('/ranobe/<int:id>')
def view_ranobe(id):
    db_sess = db_session.create_session()
    try:
        ranobe = db_sess.query(Ranobe).get(id)
        if not ranobe:
            abort(404)

        volumes = db_sess.query(Volume).filter(Volume.ranobe_id == id).order_by(Volume.volume_number).all()
        return render_template('ranobe.html', ranobe=ranobe, volumes=volumes)
    finally:
        db_sess.close()


# добавить новое ранобе
@app.route('/add_ranobe', methods=['GET', 'POST'])
@login_required
def add_ranobe():
    form = RanobeForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            ranobe = Ranobe(
                title=form.title.data,
                description=form.description.data,
                cover_image=form.cover_image.data,
                author_id=current_user.id
            )
            db_sess.add(ranobe)
            db_sess.commit()
            return redirect('/')
        finally:
            db_sess.close()
    return render_template('add_ranobe.html', form=form)


# изменение существующего
@app.route('/edit_ranobe/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_ranobe(id):
    form = RanobeForm()
    db_sess = db_session.create_session()
    try:
        ranobe = db_sess.query(Ranobe).get(id)

        if not ranobe or (current_user.id != ranobe.author_id and current_user.id != 1):
            abort(403)

        if form.validate_on_submit():
            ranobe.title = form.title.data
            ranobe.description = form.description.data
            ranobe.cover_image = form.cover_image.data
            db_sess.commit()
            return redirect(f'/ranobe/{id}')

        if request.method == 'GET':
            form.title.data = ranobe.title
            form.description.data = ranobe.description
            form.cover_image.data = ranobe.cover_image

        return render_template('add_ranobe.html', form=form, title='Редактирование ранобе')
    finally:
        db_sess.close()


# удаление существующего
@app.route('/delete_ranobe/<int:id>')
@login_required
def delete_ranobe(id):
    db_sess = db_session.create_session()
    try:
        ranobe = db_sess.query(Ranobe).get(id)

        if not ranobe or (current_user.id != ranobe.author_id and current_user.id != 1):
            abort(403)

        db_sess.delete(ranobe)
        db_sess.commit()
        return redirect('/')
    finally:
        db_sess.close()


# создание нового тома
@app.route('/ranobe/<int:ranobe_id>/new_volume', methods=['POST'])
@login_required
def new_volume(ranobe_id):
    db_sess = db_session.create_session()
    try:
        ranobe = db_sess.query(Ranobe).get(ranobe_id)

        if not ranobe or (current_user.id != ranobe.author_id and current_user.id != 1):
            abort(403)

        last_volume = db_sess.query(Volume).filter(Volume.ranobe_id == ranobe_id) \
            .order_by(Volume.volume_number.desc()).first()

        new_volume_number = last_volume.volume_number + 1 if last_volume else 1

        volume = Volume(
            volume_number=new_volume_number,
            ranobe_id=ranobe_id,
            title=f"Том {new_volume_number}"
        )
        db_sess.add(volume)
        db_sess.commit()
        return redirect(f'/ranobe/{ranobe_id}')
    finally:
        db_sess.close()


# список всех глав определенного тома
@app.route('/volume/<int:id>')
def view_volume(id):
    db_sess = db_session.create_session()
    try:
        volume = db_sess.query(Volume).get(id)
        if not volume:
            abort(404)

        chapters = db_sess.query(Chapter).filter(Chapter.volume_id == id).order_by(Chapter.chapter_number).all()
        return render_template('volume.html', volume=volume, chapters=chapters)
    finally:
        db_sess.close()


# добавление главы
@app.route('/ranobe/<int:ranobe_id>/add_chapter', methods=['GET', 'POST'])
@login_required
def add_chapter(ranobe_id):
    form = ChapterForm()
    db_sess = db_session.create_session()
    try:
        ranobe = db_sess.query(Ranobe).get(ranobe_id)

        if not ranobe or (current_user.id != ranobe.author_id and current_user.id != 1):
            abort(403)

        volume_id = request.args.get('volume_id')

        if volume_id:
            volume = db_sess.query(Volume).get(volume_id)
            if not volume or volume.ranobe_id != ranobe_id:
                abort(404)
        else:
            volume = db_sess.query(Volume).filter(
                Volume.ranobe_id == ranobe_id
            ).order_by(Volume.volume_number.desc()).first()

            if not volume:
                volume = Volume(
                    volume_number=1,
                    ranobe_id=ranobe_id,
                    title=f"Том 1"
                )
                db_sess.add(volume)
                db_sess.commit()

        if form.validate_on_submit():
            chapter = Chapter(
                title=form.title.data,
                content=form.content.data,
                chapter_number=form.chapter_number.data,
                volume_id=volume.id
            )
            db_sess.add(chapter)
            db_sess.commit()
            return redirect(f'/volume/{volume.id}')

        if volume.chapters:
            next_chapter_num = max(c.chapter_number for c in volume.chapters) + 1
        else:
            next_chapter_num = 1

        form.chapter_number.data = next_chapter_num
        return render_template('add_chapter.html', form=form, ranobe=ranobe, volume=volume)
    finally:
        db_sess.close()


# изменение главы
@app.route('/edit_chapter/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_chapter(id):
    form = ChapterForm()
    db_sess = db_session.create_session()
    try:
        chapter = db_sess.query(Chapter).get(id)

        if not chapter or (current_user.id != chapter.volume.ranobe.author_id and current_user.id != 1):
            abort(403)

        if form.validate_on_submit():
            chapter.title = form.title.data
            chapter.content = form.content.data
            chapter.chapter_number = form.chapter_number.data
            db_sess.commit()
            return redirect(f'/chapter/{id}')

        if request.method == 'GET':
            form.title.data = chapter.title
            form.content.data = chapter.content
            form.chapter_number.data = chapter.chapter_number

        return render_template('add_chapter.html',
                             form=form,
                             ranobe=chapter.volume.ranobe,
                             volume=chapter.volume,
                             title='Редактирование главы')
    finally:
        db_sess.close()


# удаление главы
@app.route('/delete_chapter/<int:id>')
@login_required
def delete_chapter(id):
    db_sess = db_session.create_session()
    try:
        chapter = db_sess.query(Chapter).get(id)

        if not chapter or (current_user.id != chapter.volume.ranobe.author_id and current_user.id != 1):
            abort(403)

        volume_id = chapter.volume.id
        db_sess.delete(chapter)
        db_sess.commit()
        return redirect(f'/volume/{volume_id}')
    finally:
        db_sess.close()


# просмотр определенной главы
@app.route('/chapter/<int:id>', methods=['GET', 'POST'])
def view_chapter(id):
    form = CommentForm()
    db_sess = db_session.create_session()
    try:
        chapter = db_sess.query(Chapter).get(id)

        if not chapter:
            abort(404)

        prev_chapter = db_sess.query(Chapter).filter(
            Chapter.volume_id == chapter.volume_id,
            Chapter.chapter_number < chapter.chapter_number
        ).order_by(Chapter.chapter_number.desc()).first()

        next_chapter = db_sess.query(Chapter).filter(
            Chapter.volume_id == chapter.volume_id,
            Chapter.chapter_number > chapter.chapter_number
        ).order_by(Chapter.chapter_number.asc()).first()

        if form.validate_on_submit() and current_user.is_authenticated:
            comment = Comment(
                content=form.content.data,
                user_id=current_user.id,
                chapter_id=id
            )
            db_sess.add(comment)
            db_sess.commit()
            return redirect(f'/chapter/{id}')

        comments = db_sess.query(Comment).filter(Comment.chapter_id == id) \
            .order_by(Comment.created_date.desc()).all()

        return render_template('chapter.html',
                             chapter=chapter,
                             prev_chapter=prev_chapter,
                             next_chapter=next_chapter,
                             comments=comments,
                             form=form)
    finally:
        db_sess.close()


# удаление коммента
@app.route('/delete_comment/<int:id>')
@login_required
def delete_comment(id):
    db_sess = db_session.create_session()
    try:
        comment = db_sess.query(Comment).get(id)

        if not comment or (current_user.id != comment.user_id and current_user.id != 1):
            abort(403)

        chapter_id = comment.chapter_id
        db_sess.delete(comment)
        db_sess.commit()
        return redirect(f'/chapter/{chapter_id}')
    finally:
        db_sess.close()


# Возвращает json со списком всех ранобе
@app.route('/api/ranobe', methods=['GET'])
def api_get_all_ranobe():
    db_sess = db_session.create_session()
    try:
        ranobe_list = db_sess.query(Ranobe).order_by(Ranobe.title).all()
        return jsonify([{
            'id': ranobe.id,
            'title': ranobe.title,
            'description': ranobe.description,
            'cover_image': ranobe.cover_image
        } for ranobe in ranobe_list])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_sess.close()


# Возвращает json со списком глав указанного тома
@app.route('/api/ranobe/<int:ranobe_id>/volumes/<int:volume_number>/chapters', methods=['GET'])
def api_get_volume_chapters(ranobe_id, volume_number):
    db_sess = db_session.create_session()
    try:
        volume = db_sess.query(Volume).filter(
            Volume.ranobe_id == ranobe_id,
            Volume.volume_number == volume_number
        ).first()

        if not volume:
            return jsonify({'error': 'Volume not found'}), 404

        chapters = db_sess.query(Chapter).filter(
            Chapter.volume_id == volume.id
        ).order_by(Chapter.chapter_number).all()

        return jsonify([{
            'id': chapter.id,
            'title': chapter.title,
            'chapter_number': chapter.chapter_number
        } for chapter in chapters])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_sess.close()


# Возвращает json с содержимым главы по глобальному ID главы
@app.route('/api/chapters/<int:chapter_id>', methods=['GET'])
def api_get_chapter_content(chapter_id):
    db_sess = db_session.create_session()
    try:
        chapter = db_sess.query(Chapter).get(chapter_id)
        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404

        volume = db_sess.query(Volume).get(chapter.volume_id)
        if not volume:
            return jsonify({'error': 'Volume not found'}), 404

        return jsonify({
            'id': chapter.id,
            'title': chapter.title,
            'chapter_number': chapter.chapter_number,
            'content': chapter.content,
            'volume_number': volume.volume_number,
            'ranobe_id': volume.ranobe_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_sess.close()


# Возвращает json с содержимым главы по номеру тома и номеру главы в определенном ранобе
@app.route('/api/ranobe/<int:ranobe_id>/volumes/<int:volume_number>/chapters/<int:chapter_number>', methods=['GET'])
def api_get_chapter_content2(ranobe_id, volume_number, chapter_number):
    db_sess = db_session.create_session()
    try:
        volume = db_sess.query(Volume).filter(
            Volume.ranobe_id == ranobe_id,
            Volume.volume_number == volume_number
        ).first()

        if not volume:
            return jsonify({'error': 'Volume not found'}), 404

        chapter = db_sess.query(Chapter).filter(
            Chapter.volume_id == volume.id,
            Chapter.chapter_number == chapter_number
        ).first()

        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404

        return jsonify({
            'id': chapter.id,
            'title': chapter.title,
            'chapter_number': chapter.chapter_number,
            'content': chapter.content,
            'volume_number': volume.volume_number,
            'ranobe_id': volume.ranobe_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_sess.close()


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403


def main():
    db_session.global_init("db/ranobe.db")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
