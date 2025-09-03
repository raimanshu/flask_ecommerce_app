from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from contextvars import ContextVar
from infra.environment import SQLALCHEMY_DATABASE_URI

# Keep track of current DB context
_current_session_ctx = ContextVar("current_session", default=None)

# Register DB engines
engines = {
    "sqlite": create_engine(SQLALCHEMY_DATABASE_URI, echo=False),
    "mysql": create_engine("mysql+mysqlconnector://root:Deadpool%40123@127.0.0.1:3306/awvwzjr4_rialto", echo=False),
}

# Create session factories for each engine
SessionFactories = {
    db_key: scoped_session(sessionmaker(bind=engine))
    for db_key, engine in engines.items()
}


# Set current DB for a request/thread
def set_current_db(db_key):
    if db_key not in SessionFactories:
        raise ValueError(f"Database '{db_key}' is not configured")
    _current_session_ctx.set(SessionFactories[db_key])


# Get current session
def get_session():
    session = _current_session_ctx.get()
    if session is None:
        # Default to sqlite
        session = SessionFactories["sqlite"]
    return session


# Close all sessions (optional: call this on teardown)
def close_all_sessions():
    for session in SessionFactories.values():
        session.remove()
