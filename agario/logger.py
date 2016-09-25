import logging
import logging.handlers
import os


__all__ = [
    'create_logger',
]


basedir = os.path.dirname(os.path.abspath(__file__))

DEFAULT_LEVEL = logging.DEBUG

DEFAULT_LOGFILE = os.path.join(basedir, '..', 'agario.log')

DEFAULT_FORMAT = '%(asctime)s %(module)s.py:%(lineno)d %(name)s (%(levelname)s) %(message)s'

def create_logger(name=None, filename=None, level=None, format=None):
    logger = logging.getLogger(name)
    logger.setLevel(level or DEFAULT_LEVEL)
    h = logging.FileHandler(
        filename or DEFAULT_LOGFILE,
        mode='w',
        encoding='utf-8',
        delay=True
    )
    h.setFormatter(logging.Formatter(format or DEFAULT_FORMAT))
    logger.addHandler(h)
    return logger
