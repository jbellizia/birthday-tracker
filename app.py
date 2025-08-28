from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3
from datetime import date, datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.relativedelta import relativedelta
import os
from itsdangerous import URLSafeTimedSerializer
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_DEFAULT_SENDER'] = ('Birthday', os.getenv('MAIL_USERNAME'))
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['TEMPLATES_AUTO_RELOAD'] = True


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


mail = Mail(app)

s = URLSafeTimedSerializer(app.secret_key)

DB_FILE =  os.getenv("DATABASE_PATH", "birthdays.db")
MY_EMAIL = os.getenv("MY_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", os.getenv("SECRET_KEY"))  

class Birthday:
    def __init__(self, id, name, date, age):
        self.id = id
        self.name = name
        self.date = date
        self.age = age

class Notification:
    def __init__(self, id, birthday, message, timestamp):
        self.id = id
        self.birthday = birthday
        self.message = message
        self.timestamp = timestamp
    def send(self):
        msg = Message(subject=f"Birthday Reminder: {self.birthday.name} on {self.birthday.date}",
                      recipients=[MY_EMAIL])
        msg.body = self.message
        mail.send(msg)

class Admin(UserMixin):
    id = 1 
    password = os.getenv('ADMIN_PASSWORD', os.getenv('SECRET_KEY'))

@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return Admin()
    return None


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_birthdays():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, date, age FROM birthdays ORDER BY id DESC')
    birthdays = [Birthday(row['id'], row['name'], row['date'], row['age']) for row in cursor.fetchall()]
    conn.close()
    return birthdays

def get_birthday_by_id(birthday_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, date, age FROM birthdays WHERE id = ?', (birthday_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Birthday(row['id'], row['name'], row['date'], row['age'])
    return None

def add_birthday(name, date, age):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO birthdays (name, date, age) VALUES (?, ?, ?)', (name, date, age))
    conn.commit()
    conn.close()

def update_birthday(birthday_id, name, date, age):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE birthdays SET name = ?, date = ?, age = ? WHERE id = ?', (name, date, age, birthday_id))
    conn.commit()
    conn.close()

def delete_birthday(birthday_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM birthdays WHERE id = ?', (birthday_id,))
    conn.commit()
    conn.close()

def calculate_age(birthdate_str):
    birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    today = date.today()
    age = today.year - birthdate.year
    # subtract 1 if birthday hasn't happened yet this year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    return age


def check_birthdays():
    conn = get_db_connection()
    cursor = conn.cursor()

    today_md = date.today().strftime('%m-%d')
    cursor.execute("SELECT id, name, date, age FROM birthdays WHERE strftime('%m-%d', date) = ?", (today_md,))
    rows = cursor.fetchall()

    print("DEBUG birthdays today:", rows)

    for row in rows:
        birthday = Birthday(row['id'], row['name'], row['date'], row['age'])

        try:
            # correct age as of today
            current_age = calculate_age(birthday.date)

            # update DB to the correct age
            cursor.execute("UPDATE birthdays SET age = ? WHERE id = ?", (current_age, birthday.id))

            # build message + notification
            message = f"Today is {birthday.name}'s birthday! They turn {current_age}."
            notification = Notification(None, birthday, message, datetime.utcnow())

            # send email
            try:
                notification.send()
            except Exception as e:
                app.logger.error(f"Failed to send birthday email for {birthday.name}: {e}")

            # log notification using the SAME conn/cursor
            try:
                ts = notification.timestamp.isoformat()
                cursor.execute(
                    "INSERT INTO notifications (birthday_id, message, timestamp) VALUES (?, ?, ?)",
                    (birthday.id, notification.message, ts)
                )
                notification.id = cursor.lastrowid
            except Exception as e:
                app.logger.error(f"Failed to log notification for {birthday.name}: {e}")

        except Exception as e:
            app.logger.error(f"Error processing birthday id={row['id']}: {e}")

    conn.commit()
    conn.close()


# authentication routes and protection
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pwd = request.form.get('password', '')
        admin = Admin()
        if pwd == admin.password:
            login_user(admin)
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid password', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('login'))

# protect index route
@app.route('/')
@login_required
def index():
    birthdays = get_birthdays()
    return render_template('index.html', birthdays=birthdays)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        date_str = request.form['date']

        try:
            dob = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('add'))

        today = date.today()
        age = relativedelta(today, dob).years

        if not name or not date_str or age is None:
            flash('All fields are required!', 'error')
            return redirect(url_for('add'))
        add_birthday(name, date_str, age)
        flash('Birthday added successfully!', 'success')
        return redirect(url_for('add'))
    return render_template('add.html')

@app.route('/edit/<int:birthday_id>', methods=['GET', 'POST'])
@login_required
def edit(birthday_id):
    birthday = get_birthday_by_id(birthday_id)
    if not birthday:
        flash('Birthday not found!', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        date_str = request.form['date']

        try:
            dob = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('add'))

        today = date.today()
        age = relativedelta(today, dob).years

        if not name or not date_str or age is None:
            flash('All fields are required!', 'error')
            return redirect(url_for('add'))
        update_birthday(birthday_id, name, date_str, age)
        flash('Birthday edited successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', birthday=birthday)

@app.route('/delete/<int:birthday_id>', methods=['POST'])
@login_required
def delete(birthday_id):
    birthday = get_birthday_by_id(birthday_id)
    if not birthday:
        flash('Birthday not found!', 'error')
        return redirect(url_for('index'))
    delete_birthday(birthday_id)
    flash('Birthday deleted successfully!', 'success')
    return redirect(url_for('index'))   

@app.route("/debug-check")
@login_required
def debug_check():
    check_birthdays()
    return "check_birthdays() ran — check logs/DB!"

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_birthdays, trigger="cron", hour=7)
scheduler.start()


# For development only:
# app.run(debug=True, host='0.0.0.0', port=5002)