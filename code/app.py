from flask import Flask, render_template

from flask_cors import CORS
from flask_talisman import Talisman
from flask_wtf import CSRFProtect

from config import Config
from infra.environment import (
    SECRET_KEY,
    # SQLALCHEMY_DATABASE_URI,
    DEBUG_MODE,
    DB_PORT,
    DB_HOST,
)
from infra.database import db
from infra.db_config import config_by_name

app = Flask(__name__)

CORS(app)
csrf = CSRFProtect()
csrf.init_app(app)
Talisman(app, frame_options="DENY")


# app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config['SECRET_KEY'] = SECRET_KEY

app.config.from_object(config_by_name['sqlite'])
db.init_app(app)


"""
init_db(app)


from flask import Blueprint, jsonify
from database import mongo

bp = Blueprint("mongo_users", __name__)

@bp.route("/mongo-users")
def get_users():
    users = mongo.db.users.find()
    return jsonify([user for user in users])

"""
# app.config.from_object(Config)


@app.route("/")
@app.route("/index")
def index():
    return "This is the base URL showing server is working fine. Good to go!!"


# @app.route("/profile", methods=["GET", "POST"])
# def profile():
#     user = {"username": "Miguel"}
#     posts = [
#         {"author": {"username": "John"}, "body": "Beautiful day in Portland!"},
#         {"author": {"username": "Susan"}, "body": "The Avengers movie was so cool!"},
#     ]
#     # return render_template("profile.html", title="profile", user=user, posts=posts)
#     return render_template("dummy.html", data={"title": "Profile", "user": user, "posts": posts})

with app.app_context():

    from web.blueprints.entity_routes import entity_route
    from web.blueprints.authentication_routes import auth_route

    app.register_blueprint(entity_route, url_prefix="/api")
    app.register_blueprint(auth_route, url_prefix="/authenticate")
    # app.register_blueprint(entity_route, url_prefix="/dashboard")
    # app.register_blueprint(entity_route, url_prefix="/admin")


if __name__ == "__main__":
    # print(app.__dict__)
    app.run(debug=DEBUG_MODE, port=DB_PORT, host=DB_HOST)
