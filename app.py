import sqlite3
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, session)

app = Flask(__name__)
app.secret_key = 'health_center_secret_key_2025'

DB_NAME = 'database.db'

# ---------- Данные для входа в админку ----------
ADMIN_LOGIN = 'admin'
ADMIN_PASSWORD = 'admin123'


# ---------- Работа с базой ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            experience INTEGER,
            description TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            details TEXT,
            price REAL,
            duration INTEGER
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            service TEXT,
            date TEXT,
            comment TEXT,
            status TEXT DEFAULT 'новая',
            created_at TEXT
        )
    ''')

    cur.execute('SELECT COUNT(*) FROM doctors')
    if cur.fetchone()[0] == 0:
        cur.executemany('''
            INSERT INTO doctors (full_name, specialization, experience, description)
            VALUES (?, ?, ?, ?)
        ''', [
            ('Иванова Анна Петровна', 'Терапевт', 15, 'Специалист по внутренним болезням, высшая категория.'),
            ('Петров Сергей Иванович', 'Кардиолог', 20, 'Кандидат медицинских наук, специалист по сердечно-сосудистым заболеваниям.'),
            ('Сидорова Мария Олеговна', 'Невролог', 12, 'Специалист по заболеваниям нервной системы.'),
            ('Кузнецов Дмитрий Андреевич', 'Стоматолог', 8, 'Терапевтическая и эстетическая стоматология.'),
        ])

    cur.execute('SELECT COUNT(*) FROM services')
    if cur.fetchone()[0] == 0:
        cur.executemany('''
            INSERT INTO services (name, description, details, price, duration)
            VALUES (?, ?, ?, ?, ?)
        ''', [
            ('Консультация терапевта',
             'Первичный приём, осмотр, назначения.',
             'Терапевт проведёт осмотр, измерит давление, выслушает жалобы, при необходимости назначит дополнительные обследования и даст рекомендации по лечению. Длительность приёма — 30 минут. В стоимость входит консультация и план лечения.',
             1500, 30),

            ('Консультация кардиолога',
             'Приём с расшифровкой ЭКГ.',
             'Кардиолог проведёт осмотр, измерит артериальное давление, сделает и расшифрует ЭКГ, оценит работу сердца и сосудов. По результатам даст рекомендации и, при необходимости, назначит лечение или дополнительные исследования (ЭхоКГ, холтер-мониторинг).',
             2200, 40),

            ('УЗИ',
             'Ультразвуковое исследование внутренних органов.',
             'Современное УЗИ-оборудование позволяет точно и безопасно исследовать внутренние органы: печень, почки, поджелудочную железу, щитовидную железу, органы малого таза и другие. Исследование безболезненное, без вредного излучения. Заключение выдаётся сразу после процедуры.',
             1800, 30),

            ('Общий анализ крови',
             'Забор крови и лабораторное исследование.',
             'Общий анализ крови показывает уровень гемоглобина, количество эритроцитов, лейкоцитов, тромбоцитов, СОЭ. Помогает выявить анемию, воспалительные процессы, инфекции. Результат готов в течение 1 рабочего дня. Забор крови проводится одноразовыми стерильными инструментами.',
             700, 15),

            ('Лечение зуба',
             'Терапевтическое лечение кариеса.',
             'Лечение кариеса включает: диагностику, анестезию, удаление поражённых тканей, пломбирование и шлифовку. Используются современные светоотверждаемые пломбы, подобранные под цвет ваших зубов. Приём проходит комфортно и безболезненно.',
             3500, 60),
        ])

    conn.commit()
    conn.close()


# ---------- Проверка авторизации ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Сначала войдите в админ-панель.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


# ---------- Публичные страницы ----------
@app.route('/')
def index():
    conn = get_db()
    doctors = conn.execute('SELECT * FROM doctors LIMIT 3').fetchall()
    services = conn.execute('SELECT * FROM services LIMIT 4').fetchall()
    conn.close()
    return render_template('index.html', doctors=doctors, services=services)


@app.route('/services')
def services():
    conn = get_db()
    services = conn.execute('SELECT * FROM services').fetchall()
    conn.close()
    return render_template('services.html', services=services)


@app.route('/doctors')
def doctors():
    conn = get_db()
    doctors = conn.execute('SELECT * FROM doctors').fetchall()
    conn.close()
    return render_template('doctors.html', doctors=doctors)


@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    conn = get_db()
    services_list = conn.execute('SELECT * FROM services').fetchall()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        service = request.form['service']
        date = request.form['date']
        comment = request.form.get('comment', '')

        conn.execute('''
            INSERT INTO appointments (name, phone, service, date, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, phone, service, date, comment, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        conn.close()

        flash('Ваша заявка принята! Мы свяжемся с вами в ближайшее время.', 'success')
        return redirect(url_for('appointment'))

    conn.close()
    return render_template('appointment.html', services=services_list)


@app.route('/contacts')
def contacts():
    return render_template('contacts.html')


# ---------- Вход / выход ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_LOGIN and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Вы вошли в админ-панель.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Неверный логин или пароль.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Вы вышли из админ-панели.', 'success')
    return redirect(url_for('index'))


# ---------- Админ-панель (защищена) ----------
@app.route('/admin')
@login_required
def admin():
    conn = get_db()
    appointments = conn.execute('SELECT * FROM appointments ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', appointments=appointments)


@app.route('/admin/appointment/delete/<int:id>')
@login_required
def delete_appointment(id):
    conn = get_db()
    conn.execute('DELETE FROM appointments WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Заявка удалена.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/doctors', methods=['GET', 'POST'])
@login_required
def admin_doctors():
    conn = get_db()
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO doctors (full_name, specialization, experience, description)
            VALUES (?, ?, ?, ?)
        ''', (request.form['full_name'], request.form['specialization'],
              request.form['experience'], request.form['description']))
        conn.commit()
        flash('Врач добавлен.', 'success')

    doctors = conn.execute('SELECT * FROM doctors').fetchall()
    conn.close()
    return render_template('admin_doctors.html', doctors=doctors)


@app.route('/admin/doctors/delete/<int:id>')
@login_required
def delete_doctor(id):
    conn = get_db()
    conn.execute('DELETE FROM doctors WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Врач удалён.', 'success')
    return redirect(url_for('admin_doctors'))


@app.route('/admin/services', methods=['GET', 'POST'])
@login_required
def admin_services():
    conn = get_db()
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO services (name, description, details, price, duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (request.form['name'], request.form['description'],
              request.form.get('details', ''), request.form['price'],
              request.form['duration']))
        conn.commit()
        flash('Услуга добавлена.', 'success')

    services = conn.execute('SELECT * FROM services').fetchall()
    conn.close()
    return render_template('admin_services.html', services=services)


@app.route('/admin/services/delete/<int:id>')
@login_required
def delete_service(id):
    conn = get_db()
    conn.execute('DELETE FROM services WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Услуга удалена.', 'success')
    return redirect(url_for('admin_services'))


# ---------- Запуск ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)