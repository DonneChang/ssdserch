import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

formatter = logging.Formatter(
    "[%(levelname)s] %(asctime)s - %(filename)s:%(lineno)d - %(message)s"
)

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)