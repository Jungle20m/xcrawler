import logging
import os
from logging.handlers import TimedRotatingFileHandler

formatter = "%(asctime)s - %(levelname)s - %(message)s"
APP_NAME = "ALPHY"
LOG_DIR = "logs"
LOG_FILE = "log.txt"

def get_logger():
    # Create logger
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Create file handler with daily rotation
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    file_handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1, backupCount=30)
    file_handler.setLevel(logging.DEBUG)
    
    # Set formatter
    ch_format = logging.Formatter(formatter)
    file_handler.setFormatter(ch_format)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger