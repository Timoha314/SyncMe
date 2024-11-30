from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'supersecretkey'  # Для работы flash-сообщений
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    instagram = db.Column(db.String(120), unique=True, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)  # Дата рождения
    gender = db.Column(db.String(10), nullable=False)  # Пол: 'Мужской' или 'Женский'

    @property
    def age(self):
        # Вычисление возраста на основе даты рождения
        today = datetime.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Получаем данные из формы
        username = request.form.get('username')
        email = request.form.get('email')
        instagram = request.form.get('instagram')
        birth_date = request.form.get('birth_date')
        gender = request.form.get('gender')

        # Проверка на заполненность полей
        if not username or not email or not instagram or not birth_date or not gender:
            flash("Все поля обязательны для заполнения.", "error")
            return redirect(url_for('register'))

        # Проверка даты рождения
        try:
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except ValueError:
            flash("Неверный формат даты. Используйте формат ГГГГ-ММ-ДД.", "error")
            return redirect(url_for('register'))

        # Проверка на существующего пользователя
        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email) |
            (User.instagram == instagram)
        ).first()

        if existing_user:
            flash("Пользователь с таким именем, email или Instagram уже существует.", "error")
            return redirect(url_for('register'))

        # Создание нового пользователя
        new_user = User(username=username, email=email, instagram=instagram, birth_date=birth_date, gender=gender)
        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            flash("Регистрация прошла успешно!", "success")
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при регистрации: {str(e)}", "error")
            return redirect(url_for('register'))

    # Отображение формы регистрации
    return render_template('register.html')


@app.route('/entrance', methods=['GET', 'POST'])
def entrance():
    if request.method == 'POST':
        instagram = request.form.get('instagram')  # Используем 'instagram', а не 'username'

        # Проверяем, что значение instagram не пустое
        if not instagram:
            flash("Введите ваш Instagram.", "error")
            return redirect(url_for('entrance'))  # Перенаправление, если нет значения

        # Ищем пользователя по Instagram
        user = User.query.filter_by(instagram=instagram).first()

        if user:
            session['user_id'] = user.id  # Сохраняем id пользователя в сессии
            flash("Вход выполнен успешно!", "success")
            return redirect(url_for('profile'))  # Перенаправление на страницу профиля
        else:
            flash("Пользователь с таким Instagram не найден. Пожалуйста, проверьте введенные данные.", "error")
            return redirect(url_for('entrance'))  # Если пользователь не найден, остаемся на странице входа

    return render_template('entrance.html')  # Показываем форму для входа

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash("Пожалуйста, войдите в систему.", "error")
        return redirect(url_for('entrance'))

    user = User.query.get(user_id)
    return render_template('profile.html', user=user)

@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            try:
                db.session.delete(user)
                db.session.commit()
                session.pop('user_id', None)  # Очистить сессию после удаления профиля
                flash("Ваш профиль был успешно удален.", "success")
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash(f"Ошибка при удалении профиля: {str(e)}", "error")
                return redirect(url_for('profile'))
    flash("Ошибка при удалении профиля.", "error")
    return redirect(url_for('profile'))

@app.route('/users')
def users():
    # Запрос всех пользователей из базы данных
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Вы вышли из системы.", "success")
    return redirect(url_for('index'))

def delete_all_users():
    try:
        # Удаляем всех пользователей
        db.session.query(User).delete()
        db.session.commit()
        flash("Все пользователи были успешно удалены.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при удалении пользователей: {str(e)}", "error")
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Удаляем все таблицы
        db.create_all()  # Создаем их заново
    app.run(debug=True)


