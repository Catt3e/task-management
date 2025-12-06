from typer import prompt
from todolist.db import get_db
from todolist.models import task as taskModel
from flask_login import current_user

class TaskController:
    def __init__(self):
        self.db = get_db()

    def append_data(self, row):
        return taskModel.Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            time_set=row['time_set'],
            expire_time=row['expire_time'],
            recurrent_type=row['recurrent_type'],
            reminder=row['reminder'],
            repeat_interval=row['repeat_interval'],
            destination=row['destination'],
            status=row['status']
        )


    def fetch_all(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM task WHERE deleted_at IS NULL AND user_id = %s", (current_user.id,))
            rows = cursor.fetchall()
        tasks = []
        for row in rows:
            task = self.append_data(row)
            tasks.append(task)
        return tasks
    
    #Finished tasks: Tasks that are marked as complete (status = 1)
    def fetch_finished(self):
        tasks = self.fetch_all()
        finished_tasks = [task for task in tasks if task.status == 1]
        return finished_tasks
    
    # Overdue tasks: Tasks that are not complete (status = 0) and have an expire_time in the past
    def fetch_overdue(self):
        tasks = self.fetch_all()
        import datetime
        overdue_tasks = [task for task in tasks if task.status == 0 and task.is_overdue()]
        return overdue_tasks
    
    # Pending tasks: Tasks that are not complete (status = 0) and are not overdue
    def fetch_pending(self):
        tasks = self.fetch_all()
        pending_tasks = [task for task in tasks if task.status == 0 and not task.is_overdue()]
        return pending_tasks
    
    # Upcoming tasks: Tasks that are not complete (status = 0) and have an expire_time within the next 7 days
    def fetch_upcoming(self):
        import datetime
        tasks = self.fetch_all()
        upcoming_tasks = [task for task in tasks if 
                          task.status == 0 and
                          not task.is_overdue() and
                           (((task.time_set - datetime.datetime.now()).days <= 7) or
                           (task.expire_time and (task.expire_time - datetime.datetime.now()).days <= 7))
                          ]
        return upcoming_tasks

    # Combined fetch: Pending + Overdue + Finished
    def fetch_combine(self):
        tasks = []
        tasks += self.fetch_pending()
        tasks += self.fetch_overdue()
        tasks += self.fetch_finished()
        return tasks
    

    def get_task_by_id(self, task_id):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM task WHERE id = %s and user_id = %s",
                (task_id, current_user.id)
            )
            row = cursor.fetchone()
        if row:
            return self.append_data(row)
        return None
    

    def add_task(self, title, time_set_raw, description=None, expire_time_raw=None, recurrent_type=None,
                 reminder_raw=None, repeat_interval_raw=None, destination=None):
        from datetime import datetime

        if time_set_raw:
            time_set = datetime.strptime(time_set_raw, '%Y-%m-%dT%H:%M')
        if expire_time_raw:
            expire_time = datetime.strptime(expire_time_raw, '%Y-%m-%dT%H:%M')
        else:
            expire_time = None

        if reminder_raw == '' or reminder_raw is None:
            reminder = None
        else:
            reminder = int(reminder_raw)

        if repeat_interval_raw == '' or repeat_interval_raw is None:
            repeat_interval = 0
        else:
            repeat_interval = int(repeat_interval_raw)

        with self.db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO task (title, description, time_set, expire_time, recurrent_type, reminder, repeat_interval, destination, status, user_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (title, description, time_set, expire_time, recurrent_type, reminder, repeat_interval, destination, 0, current_user.id)
            )
        self.db.commit()


    def edit_task(self, task_id, title, time_set_raw, description=None, expire_time_raw=None, recurrent_type=None,
                  reminder_raw=None, repeat_interval_raw=None, destination=None):
        from datetime import datetime

        if time_set_raw:
            time_set = datetime.strptime(time_set_raw, '%Y-%m-%dT%H:%M')
        if expire_time_raw:
            expire_time = datetime.strptime(expire_time_raw, '%Y-%m-%dT%H:%M')
        else:
            expire_time = None

        if reminder_raw == '' or reminder_raw is None:
            reminder = None
        else:
            reminder = int(reminder_raw)

        if repeat_interval_raw == '' or repeat_interval_raw is None:
            repeat_interval = 0
        else:
            repeat_interval = int(repeat_interval_raw)

        with self.db.cursor() as cursor:
            cursor.execute(
                "UPDATE task SET title = %s, description = %s, time_set = %s, expire_time = %s, recurrent_type = %s, reminder = %s, repeat_interval = %s, destination = %s, updated_at = NOW() WHERE id = %s",
                (title, description, time_set, expire_time, recurrent_type, reminder, repeat_interval, destination, task_id)
            )
        self.db.commit()


    def soft_delete_task(self, task_id):
        with self.db.cursor() as cursor:
            cursor.execute(
                "UPDATE task SET deleted_at = NOW() WHERE id = %s",
                (task_id,)
            )
        self.db.commit()


    def complete_task(self, task_id):
        with self.db.cursor() as cursor:
            cursor.execute(
                "UPDATE task SET status = 1, updated_at = NOW() WHERE id = %s",
                (task_id,)
            )
        self.recurrent_handler(task_id)
        
        result = self.db.commit()
        if result:
            return True


    def terminate_task(self, task_id):
        with self.db.cursor() as cursor:
            cursor.execute(
                "UPDATE task SET recurrent_type = -1, updated_at = NOW() WHERE id = %s",
                (task_id,)
            )
        self.db.commit()


    def search_tasks(self, keyword):
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM task WHERE (title LIKE %s OR description LIKE %s or destination LIKE %s or time_set LIKE %s) AND deleted_at IS NULL and user_id = %s",
                ('%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', current_user.id)
            )
            rows = cursor.fetchall()
        tasks = []
        for row in rows:
            task = self.append_data(row)
            tasks.append(task)
        return tasks
    

    def recurrent_handler(self, task_id):
        import datetime
        import math
        task = self.get_task_by_id(task_id)
        if not task:
            return False

        if task.recurrent_type == -1:
            return False

        new_time_set = None
        new_expire_time = None

        task_duration = None
        

        if task.recurrent_type == 0:  # Daily
            if task.time_set:
                if task.time_set > datetime.datetime.now():
                    new_time_set = task.time_set + datetime.timedelta(days=1)
                else:
                    new_time_set = datetime.datetime.now() + datetime.timedelta(days=1)
            

        elif task.recurrent_type == 1:  # Weekly
            if task.time_set:
                if task.time_set > datetime.datetime.now():
                    new_time_set = task.time_set + datetime.timedelta(weeks=1)
                else:
                    weeks_passed = math.ceil((datetime.datetime.now() - task.time_set).days / 7)
                    if weeks_passed < 1:
                        weeks_passed = 1
                    new_time_set = task.time_set + datetime.timedelta(weeks=weeks_passed)

        elif task.recurrent_type == 2:  # Monthly
            if task.time_set:
                day = task.time_set.day
                new_time_set = datetime.datetime.now().replace(day=day)
                if new_time_set <= datetime.datetime.now():
                    new_time_set = new_time_set.replace(month=new_time_set.month + 1)
                # Could still be invalid if next month has fewer days (Ex: 31st Jan can't move to 31st Feb)
                while True:
                    try:
                        new_time_set = new_time_set.replace(day=day)
                        break
                    except ValueError:
                        day -= 1

        elif task.recurrent_type == 3:  # Yearly
            if task.time_set:
                new_time_set = datetime.datetime.now().replace(month=task.time_set.month, day=task.time_set.day)
                if new_time_set <= datetime.datetime.now():
                    new_time_set = new_time_set.replace(year=new_time_set.year + 1)

        if task.expire_time:
                task_duration = task.expire_time - task.time_set
        new_expire_time = new_time_set + task_duration if task_duration and new_time_set else None

        with self.db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO task (title, description, time_set, expire_time, recurrent_type, reminder, repeat_interval, destination, status, user_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (task.title, task.description, new_time_set, new_expire_time, task.recurrent_type,
                 task.reminder, task.repeat_interval, task.destination, 0, current_user.id)
            )
        self.db.commit()
        return True
    

    # Thêm task nhanh từ prompt đã xử lý NLP
    def add_tasktask_quick(self, prompt, result):
        from datetime import datetime

        title = result.get("title") if result.get("title") else prompt
        dt = result.get("datetime")

        formatted = dt.strftime("%Y-%m-%dT%H:%M")
        recurrent_type = result.get("repetitive_task", -1)

        self.add_task(title=title, time_set_raw=formatted, recurrent_type=recurrent_type, description="Added via quick prompt")