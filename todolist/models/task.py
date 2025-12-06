from datetime import datetime

class Task:
    # user_id(BIGINT), title(VARCHAR), description(VARCHAR), expire_time, recurrent_type, reminder, repeat_interval, destination, status
    def __init__(self, title, time_set, user_id=None, id=None, description=None, expire_time=None, recurrent_type=-1, reminder=None, repeat_interval=0, destination=None, status=0):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.time_set = time_set
        self.expire_time = expire_time
        # -1: non-recurrent (Default), 0: daily, 1: weekly, 2: monthly, 3: yearly
        self.recurrent_type = recurrent_type
        self.reminder = reminder
        self.repeat_interval = repeat_interval
        # Destination for tasks.
        self.destination = destination
        # 0: incomplete (Default), 1: complete
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = None
        self.deleted_at = None
    
    def is_overdue(self):
        if self.expire_time and self.status == 0:
            return datetime.now() > self.expire_time
        return datetime.now() > self.time_set and self.status == 0
    
    def mark_complete(self):
        self.status = 1