import logging
import sys


def setup_logging() -> logging.Logger:
    lg = logging.getLogger("app_logger")

    if not lg.handlers:
        logging.basicConfig(level=logging.DEBUG)
        log_format = logging.Formatter("%(levelname)s - %(message)s")
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(log_format)
        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(log_format)

        lg = logging.getLogger("app_logger")
        lg.addHandler(file_handler)
        lg.addHandler(stream_handler)
        lg.propagate = False

    return lg
