import os
from infra.environment import SQLALCHEMY_DATABASE_URI

from dotenv import load_dotenv
load_dotenv()


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class SQLiteDBConfig(BaseConfig):
    print(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI


class MySQLDBConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "MYSQL_DB_PATH", "mysql+mysqlconnector://root:@127.0.0.1:3306/awvwzjr4_rialto"
    )


config_by_name = {
    "sqlite": SQLiteDBConfig,
    "mysql": MySQLDBConfig,
}
