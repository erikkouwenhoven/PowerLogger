import logging
import os
from logging.handlers import RotatingFileHandler
from Utils.settings import Settings
from Application.controller import Controller


def initializeLogging(pathToFile):
    if pathToFile is None:
        pathToFile = '.'
    if not os.path.exists(pathToFile):
        os.makedirs(pathToFile)
        print('Directory {} aangemaakt'.format(pathToFile))  # Qt is nog niet in de lucht, dus geen QMessageBox
    filename = Settings().logging_filename()
    filepath = os.path.join(pathToFile, filename)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)s %(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=filepath,
                        filemode='w')
    logging.getLogger().addHandler(RotatingFileHandler(filepath, maxBytes=100000, backupCount=10))
    logging.getLogger("PyQt6").setLevel(logging.CRITICAL)
    logging.getLogger('matplotlib').setLevel(logging.CRITICAL)
    logging.getLogger("apscheduler").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.info('Start application')


if __name__ == "__main__":
    initializeLogging(Settings().logging_path())
    Controller()
