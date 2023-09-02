import logging
import serial
import serial.tools.list_ports
from P1System.serial_settings import SerialSettings


class SerialReader:
    """
        Class for scanning the serial port either continuously or only once
    """

    def __init__(self, serial_settings: SerialSettings):
        ports = list(serial.tools.list_ports.comports())
        logging.info("Available ports:")
        for port in ports:
            logging.debug(f"  {port.name}")
        self.port = self.initPort(serial_settings)
        self.stop_running = False  # for signalling to stop running

    @staticmethod
    def initPort(serial_settings: SerialSettings):
        try:
            port = serial.Serial(
                port=serial_settings.port,
                baudrate=serial_settings.baudrate,
                parity=serial_settings.parity,
                stopbits=serial_settings.stopbits,
                bytesize=serial_settings.bytesize
            )
            logging.info("Serial port connected")
            return port
        except serial.SerialException:
            logging.error("SerialException on initialization")

    # def runContinuously(self, callback):
    #     if self.port:
    #         self.stop_running = False
    #         while self.stop_running is False:
    #             try:
    #                 line = self.port.readline()
    #                 logging.debug(f"Serial data: {line}")
    #                 print(f"Serial data: {line}")
    #                 callback(line)
    #             except serial.SerialException:
    #                 logging.error("SerialException while reading")
    #
    def getLine(self):
        if self.port:
            try:
                line = self.port.readline()
                return line
            except serial.SerialException:
                logging.error("SerialException while reading")

    # def stopRunning(self):
    #     assert self.stop_running is False
    #     self.stop_running = True
