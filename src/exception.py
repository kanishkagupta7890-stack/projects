import sys
import traceback
from src.logger import logging


def error_message_detail(error, error_detail: tuple):
    """
    Generate a detailed error message with file name, line number, and error.
    
    Args:
        error: The exception object
        error_detail: Tuple containing (type, value, traceback) from sys.exc_info()
    
    Returns:
        str: Formatted error message
    """
    _, _, exc_tb = error_detail
    file_name = exc_tb.tb_frame.f_code.co_filename
    error_message = "Error occurred in python script name [{0}] line number [{1}] error message [{2}]".format(
        file_name, exc_tb.tb_lineno, str(error)
    )
    
    return error_message


class CustomException(Exception):
    def __init__(self, error_message, error_detail: tuple):
        super().__init__(error_message)
        self.error_message = error_message_detail(error_message, error_detail)
        
        # Log the error using the logger
        logging.error(self.error_message)
    
    def __str__(self):
        return self.error_message

