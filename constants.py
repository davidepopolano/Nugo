import logging
import sys
from logging.handlers import TimedRotatingFileHandler


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight',encoding="utf-8")
    file_handler.setFormatter(FORMATTER)
    return file_handler


def init_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler())
    logger.propagate = False
    return logger


DB_USER = "root"
DB_PASSWORD = "password"
DB_HOST = "127.0.0.1"
DB_NAME = "nugodatabase"

FORMATTER = logging.Formatter("%(asctime)s — [%(filename)s:%(lineno)s - %(funcName)20s()] — %(levelname)s — %(message)s")
LOG_FILE = "res/logs/debug.log"

PATH_TO_SELECTORS = "res/xpaths/selectors.json"
PATH_TO_PARAMS = "res/xpaths/params.json"
PATH_TO_INPUT = "res/input/input.txt"
PATH_TO_CREDENTIALS = "res/credentials/credentials.yaml"
LOGGER = init_logger()







