import os
from pathlib import Path

# all configs will get without this code also. But, may get None sometime in production
from dotenv import load_dotenv
load_dotenv()

'''
Creating a database path relative to the project root.
'''
# Get project root relative to this file (e.g. code/infra/)
current_file_dir = Path(__file__).resolve().parent
project_root = current_file_dir.parent.parent  # goes to the project root

# SQLITE : Join with relative path (this path should not start with / or ../)
relative_db_path = os.environ.get("SQLITE_DATABASE_PATH", "code/infra/database/app.db")
db_absolute_path = (project_root / relative_db_path).resolve()

# SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///../users.db")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_absolute_path}"
SQLALCHEMY_DATABASE_PATH = str(db_absolute_path)





'''
import os
from pathlib import Path

# Get root
current_file_dir = Path(__file__).resolve().parent
project_root = current_file_dir.parent.parent

# Configurable database engine: sqlite, mysql, postgres, mongo
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()

# SQLite
relative_db_path = os.getenv("SQLITE_PATH", "code/infra/database/app.db")
sqlite_path = (project_root / relative_db_path).resolve()

# SQLAlchemy URIs
SQLALCHEMY_DATABASE_URI = {
    "sqlite": f"sqlite:///{sqlite_path}",
    "mysql": os.getenv("MYSQL_URI", "mysql+pymysql://user:pass@localhost/db"),
    "postgres": os.getenv("POSTGRES_URI", "postgresql://user:pass@localhost/db"),
}.get(DB_ENGINE, f"sqlite:///{sqlite_path}")  # default to sqlite

# MongoDB URI
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/appdb")

# Make all config accessible
DATABASE_CONFIG = {
    "engine": DB_ENGINE,
    "sqlalchemy_uri": SQLALCHEMY_DATABASE_URI,
    "mongodb_uri": MONGODB_URI,
}


'''










'''
Default configurations for Flask application.
'''
SECRET_KEY = os.environ.get("SECRET_KEY", "NO_ENVIRONMENT_FOUND")
SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS", "False")
