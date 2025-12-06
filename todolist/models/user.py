from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, hash_password, email):
        self.id = str(id)
        self.username = username
        self.email = email
        self.hash_password = hash_password

