from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from todolist.models.user import User
from .db import get_db
from todolist.controller.taskController import TaskController
from flask_login import login_required, login_user, current_user
from werkzeug.security import check_password_hash
from flask_login import logout_user

from todolist.controller.promptController import PromptController


bp = Blueprint('todolist', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index(message=None):
    if current_user.is_anonymous:
        return render_template('starting.html')

    tasks = TaskController().fetch_combine()

    print("Logged in as:", current_user.username)

    # default view is calendar
    view = request.args.get("view", "calendar")

    upcoming_tasks = TaskController().fetch_upcoming()

    return render_template('index.html', tasks=tasks, view=view, upcoming_tasks=upcoming_tasks, message=message)

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    TaskController().soft_delete_task(id)
    return redirect(url_for('todolist.index'))

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    from todolist.models import task as taskModel
    from datetime import datetime

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        time_set_raw = request.form.get('time_set')
        expire_time_raw = request.form.get('expire_time')
        recurrent_type = request.form.get('recurrent_type', -1)
        reminder_raw = request.form.get('reminder', None)
        repeat_interval_raw = request.form.get('repeat_interval', 0)
        destination = request.form.get('destination', None)

        TaskController().add_task(title, time_set_raw, description, expire_time_raw, recurrent_type,
                                  reminder_raw, repeat_interval_raw, destination)
        return redirect(url_for('todolist.index'))

    return render_template('addTask.html')

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    if request.method == 'GET':
        view = request.args.get("view", "calendar")
        task = TaskController().get_task_by_id(id)
        upcoming_tasks = TaskController().fetch_upcoming()
        if not task:
            return "Task not found.", 404
        return render_template('index.html', tasks=TaskController().fetch_combine(), view=view, edit_task=task, upcoming_tasks=upcoming_tasks)
    
    from todolist.models import task as taskModel
    from datetime import datetime

    task = TaskController().get_task_by_id(id)
    if not task:
        return "Task not found.", 404

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        time_set_raw = request.form.get('time_set')
        expire_time_raw = request.form.get('expire_time')
        recurrent_type = request.form.get('recurrent_type', -1)
        reminder_raw = request.form.get('reminder', None)
        repeat_interval_raw = request.form.get('repeat_interval', 0)
        destination = request.form.get('destination', None)

        TaskController().edit_task(id, title, time_set_raw, description, expire_time_raw,
                                   recurrent_type, reminder_raw, repeat_interval_raw, destination)
        return redirect(url_for('todolist.index'))

    return render_template('editTask.html', task=task)


@bp.route('/search', methods=['GET'])
@login_required
def search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return redirect(url_for('todolist.index'))
    tasks = TaskController().search_tasks(keyword)
    view = request.args.get("view", "calendar")
    return render_template('index.html', tasks=tasks, view=view)

@bp.route('/renew/<int:id>')
@login_required
def renew_task(id):
    TaskController().recurrent_handler(id)
    return redirect(url_for('todolist.index'))

@bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    TaskController().complete_task(id)
    return redirect(url_for('todolist.index'))

@bp.route("/add/normal")
@login_required
def add_task_normal():
    return render_template("addTask.html")


@bp.route("/add/quick", methods=['GET', 'POST'])
@login_required
def add_task_quick():
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        # TaskController().add_task_quick(prompt)
        words = PromptController.extract(prompt=prompt)
        # message = words["datetime"]
        print(words)
        TaskController().add_tasktask_quick(prompt=prompt, result=words)
        return index(message= "Extracted time: " + str(words["datetime"]))
    return render_template("addTask_quick.html")









@bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email_or_username = request.form.get('email_or_username')
        password = request.form.get('password')

        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, hash_password, email FROM user WHERE (email=%s OR username=%s) AND hash_password=%s", (email_or_username, email_or_username, password))
            row = cursor.fetchone()

        if not row:
            return render_template('login.html', message="Invalid credentials.")
        else:
            print("Test 1:", row)

        user = User(row['id'], row['username'], row['hash_password'], row['email'])
        print("Test 2:", user.id, user.username, user.email)
        # if not check_password_hash(user.hash_password, password):
        #     return "Wrong password."

        login_user(user)
        print("Logged in as:", current_user.username)
        return redirect(url_for('todolist.index'))

    return render_template('login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return index()

@bp.route("/register", methods=["GET","POST"])
def register():
    # from werkzeug.security import generate_password_hash

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # hash_password = generate_password_hash(password)
        if check_duplicate(username, email):
            return render_template('register.html', message="Username or email already exists.")
        
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO user (username, email, hash_password) VALUES (%s, %s, %s)", (username, email, password))
            conn.commit()

        return redirect(url_for('todolist.login'))

    return render_template('register.html')

def check_duplicate(username, email):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM user WHERE username=%s OR email=%s", (username, email))
        row = cursor.fetchone()
        return row is not None
    








from datetime import datetime, timedelta
@bp.route('/api/reminders')
@login_required
def get_reminders():
    global notified_task_ids
    now = datetime.now()
    upcoming = now + timedelta(minutes=5)  # nhắc trước 5 phút

    tasks = TaskController().fetch_all()
    reminders = []
    notified_task_ids = set()
    

    for task in tasks:
        if task.reminder is None or task.status != 0:
            continue

        reminder_time = task.time_set - timedelta(minutes=task.reminder)

        # Chỉ nhắc task chưa nhắc lần nào trong phiên
        if now <= reminder_time <= upcoming and task.id not in notified_task_ids:
            reminders.append({
                "id": task.id,
                "title": task.title,
                "reminder": reminder_time.strftime("%Y-%m-%d %H:%M:%S")
            })
            notified_task_ids.add(task.id)

    return jsonify(reminders) 