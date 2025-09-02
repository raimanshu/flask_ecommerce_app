
import os
import sys
from datetime import datetime, time, timedelta

from loguru import logger
from utils.constants import LOG_AUDITS, LOG_DEBUG


# Remove all previously added handlers, including loguru's default handler.
logger.remove()

# Ensure the 'logs' directory exists to store log files.
os.makedirs("logs", exist_ok=True)
# LOG_LEVEL = LOG_WARNING if ENVIRONMENT == ENV_PROD else LOG_DEBUG

# LOG_LEVEL is set to LOG_DEBUG, preferred for many development environments.
LOG_LEVEL = LOG_DEBUG


class Rotator:
    def __init__(self, *, size, at):
        now = datetime.now()

        self._size_limit = size
        self._time_limit = now.replace(
            hour=at.hour, minute=at.minute, second=at.second
        )

        # If the current time is past the rotation time, schedule the next rotation for one day later.
        if now >= self._time_limit:
            self._time_limit += timedelta(days=1)

    def should_rotate(self, message, file):
        file.seek(0, 2)
        # Rotate if file size limit exceeded or the current message's timestamp is past the time limit.
        if file.tell() + len(message) > self._size_limit:
            return True
        if message.record["time"].timestamp() > self._time_limit.timestamp():
            self._time_limit += timedelta(days=1)
            return True
        return False
    
# Initialize the Rotator object with a 500 MB file size limit or rotation at midnight.
rotator = Rotator(size=5e8, at=time(0, 0, 0))

# Configure the logger to add a specific handler for file logging with the above rotator.
logger.add(
    "./logs/log_file.log",
    rotation=rotator.should_rotate,
    level=LOG_LEVEL,
    retention="30 days",
    backtrace=True,  # if ENVIRONMENT == ENV_PROD else True,
    diagnose=True,  # if ENVIRONMENT == ENV_PROD else True,
)

# Define a new log level 'LOG_AUDITS' with distinct settings for auditing logs.
logger.level(LOG_AUDITS, no=33, color="<blue>")
logger.add(sys.stdout, level=LOG_LEVEL)