import logging
import os
from logging.handlers import RotatingFileHandler
from Utils.settings import Settings
from Application.application import Application
# import faulthandler


def initialize_logging(path_to_file):
    if path_to_file is None:
        path_to_file = '.'
    if not os.path.exists(path_to_file):
        os.makedirs(path_to_file)
        print('Directory {} aangemaakt'.format(path_to_file))
    filename = Settings().logging_filename()
    filepath = os.path.join(path_to_file, filename)
    logging.getLogger().setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(filepath,
                                                   mode='w',
                                                   maxBytes=1000000,
                                                   backupCount=30)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    logging.getLogger("PyQt6").setLevel(logging.CRITICAL)
    logging.getLogger('matplotlib').setLevel(logging.CRITICAL)
    logging.getLogger("apscheduler").setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.info('Start application')


if __name__ == "__main__":
    # faulthandler.enable()
    initialize_logging(Settings().logging_path())
    Application()
