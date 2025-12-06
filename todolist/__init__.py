import os
from flask import Flask, render_template

from todolist.db import get_db
from todolist.models.user import User

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # default config
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    # load config.py if it exists
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register todo blueprint
    from . import todolist as todo
    app.register_blueprint(todo.bp)


    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'todolist.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # query user by id from your DB
        import pymysql
        conn = get_db()  # however you get your db

        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, hash_password, email FROM user WHERE id=%s", (user_id,))
            row = cursor.fetchone()

        if row:
            return User(row['id'], row['username'], row['hash_password'], row['email'])
        return None


    @app.errorhandler(404)
    def not_found(error):
        return render_template("error/404.html"), 404


    return app

