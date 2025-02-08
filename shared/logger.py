import logging
import logging.handlers
import os
from config.config import Config
import traceback

class StackTraceFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
    
    def format(self, record):
        formatted = super().format(record)
        if record.levelno == logging.ERROR and record.exc_info:
            # Only add traceback if exc_info is available
            formatted += '\n' + ''.join(traceback.format_exception(*record.exc_info))
        return formatted

def setup_logger(name, env='debug'):
    logger = logging.getLogger(name)
    log_level = logging.DEBUG if env == 'debug' else logging.INFO
    logger.setLevel(logging.DEBUG)  # Set to lowest level to catch all logs
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)  # Use environment-based level
    console_formatter = StackTraceFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # File handler - always log everything to file
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, f'{name}.log'),
        maxBytes=1024*1024,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_formatter = StackTraceFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
