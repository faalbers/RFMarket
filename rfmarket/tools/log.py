from functools import wraps
import logging

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

def initLogger(logLevel=WARNING):
        logger = logging.getLogger('rfmarket')
        handler = logging.FileHandler('rfmarket.log', mode='w')
        formatter = logging.Formatter('%(asctime)s: %(levelname)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logLevel)

def info(message):
    if 'rfmarket' in logging.root.manager.loggerDict:
        logging.getLogger('rfmarket').info(message)

def debug(message):
    if 'rfmarket' in logging.root.manager.loggerDict:
        logging.getLogger('rfmarket').debug(message)

def exception(message):
    if 'rfmarket' in logging.root.manager.loggerDict:
        logging.getLogger('rfmarket').exception(message)

def error(message):
    if 'rfmarket' in logging.root.manager.loggerDict:
        logging.getLogger('rfmarket').error(message)

    
def indent_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        debug('Enter: %s()' % func.__name__)
        # for val in args:
        #     print(val)
        # logger = get_indented_logger('rfmarket')
        # logger.debug(f'Entering {func.__name__}()')

        # with IndentationContext():
        #     result = func(*args, **kwargs)

        # logger.debug(f'Exiting {func.__name__}()')
        
        result = func(*args, **kwargs)
        return result

    return wrapper

