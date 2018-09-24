import logging
import os


def setup_logger(log_level=None):
    directory = setup_runtime_log_directory()
    log_file = os.path.join(directory, 'runtime.log')
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        "%(asctime)s;%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(log_level or os.environ.get("LOG_LEVEL", "INFO"))
    root.addHandler(handler)


def setup_runtime_log_directory():
    main_dir = os.path.dirname(os.path.dirname(__file__))
    log_file_dir = os.path.join(main_dir, 'logs', 'system')
    if not os.path.isdir(log_file_dir):
        os.mkdir(log_file_dir)
    return log_file_dir
