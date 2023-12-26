import sys,os
sys.path.append(os.getcwd())
import logging
import src.EmailSender as EmailSender
from datetime import datetime

logger = logging.getLogger(__name__)

class CustomHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            EmailSender.boardcase_email(f"{record.levelname}", f"Time: {record.asctime}\nMessage: {record.message}\nFilename: {record.filename}\nModule: {record.module}")
        # Notifyer.notify()
            
def setup_logging():
    # Create logs directory if it doesn't exist
    log_directory = "./logs"
    os.makedirs(log_directory, exist_ok=True)

    # Log file name with a timestamp
    log_filename = datetime.now().strftime("%Y%m%d_%H%M%S.log")
    log_filepath = os.path.join(log_directory, log_filename)

    # Custom date format for the logs
    date_format = "%Y-%m-%d %H:%M:%S"

    # Basic logging configuration
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt=date_format,
                        handlers=[
                            logging.FileHandler(log_filepath),
                            logging.StreamHandler(),
                            CustomHandler()
                        ])

    return logging.getLogger()

def getLogger(name:str) -> logging.Logger:
    return logging.getLogger(name)

# Test
if __name__ == '__main__':
    logger = setup_logging()
    logger.info("This is an info message")        # Won't trigger the custom handler
    logger.warning("This is a warning message")  # Will trigger the custom handler
    logger.error("This is an error message")     # Will trigger the custom handler


