from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'supersecretkey'  # Для работы flash-сообщений
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()

        if existing_user:
            flash("Пользователь с таким именем или email уже существует.", "error")
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id  # Сохранение id пользователя в сессии
            flash("Регистрация прошла успешно!", "success")
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при регистрации: {str(e)}", "error")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/entrance', methods=['GET', 'POST'])
def entrance():
    if request.method == 'POST':
        username = request.form['username']

        # Проверка наличия пользователя в базе данных
        user = User.query.filter_by(username=username).first()
        if user:
            session['user_id'] = user.id  # Сохранение id пользователя в сессии
            flash("Вход выполнен успешно!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Неверное имя пользователя.", "error")
            return redirect(url_for('entrance'))
    return render_template('entrance.html')

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
