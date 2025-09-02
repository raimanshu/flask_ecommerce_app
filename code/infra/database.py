from flask_sqlalchemy import SQLAlchemy


# SQLite supports only one db file instance for all tables. Otherwise we need to create multiple connection like 
# users_db = SQLAlchemy()
# products_db = SQLAlchemy()


db = SQLAlchemy()


'''
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from environment import DATABASE_CONFIG

db = None  # SQLAlchemy instance
mongo = None  # PyMongo instance


def init_db(app):
    global db, mongo

    engine = DATABASE_CONFIG["engine"]

    if engine in ("sqlite", "mysql", "postgres"):
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_CONFIG["sqlalchemy_uri"]
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db = SQLAlchemy(app)
        print(f"[INFO] Connected to {engine.upper()} using SQLAlchemy.")

    elif engine == "mongodb":
        app.config["MONGO_URI"] = DATABASE_CONFIG["mongodb_uri"]
        mongo = PyMongo(app)
        print("[INFO] Connected to MongoDB using PyMongo.")

    else:
        raise ValueError(f"Unsupported DB engine: {engine}")

'''