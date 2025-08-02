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


play_logger = logging.getLogger("play")
play_log_file = Path(f"logs/play.log")
play_log_file.parent.mkdir(parents=True, exist_ok=True)   
play_logger.setLevel(logging.INFO)
file_handler = TimedRotatingFileHandler(
    play_log_file,
    encoding="utf-8",
    when="midnight",  # 按天分割（午夜时分）
    interval=1,  # 每1天轮换一次
    backupCount=7,
)
file_handler.setFormatter(formatter)
play_logger.addHandler(file_handler)
play_logger.addHandler(console_handler)
