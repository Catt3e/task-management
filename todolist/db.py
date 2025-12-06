import pymysql
from flask import current_app, g


def get_db():
    # Helpful check: fail early with a clear message if required config is missing
    required = ["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB"]
    missing = [k for k in required if not current_app.config.get(k)]
    if missing:
        raise RuntimeError(
            "Missing MySQL configuration keys: {}.\n"
            "Create an instance/config.py with these values or set them in app.config."
            .format(
                ", ".join(missing)
            )
        )

    if "db" not in g:
        g.db = pymysql.connect(
            host=current_app.config["MYSQL_HOST"],
            user=current_app.config["MYSQL_USER"],
            password=current_app.config["MYSQL_PASSWORD"],
            database=current_app.config["MYSQL_DB"],
            cursorclass=pymysql.cursors.DictCursor
        )
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()