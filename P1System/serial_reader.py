import logging
from typing import Union
import serial
import serial.tools.list_ports
from P1System.serial_settings import SerialSettings


class SerialReader:
    """
        Class for scanning the serial port either continuously or only once
    """

    def __init__(self, serial_settings: SerialSettings):
        self.serial_settings = serial_settings
        ports = list(serial.tools.list_ports.comports())
        logging.info("Available ports:")
        for port in ports:
            logging.debug(f"  {port.name}")
        self.port: serial.Serial = self.init_port(serial_settings)
        self.stop_running = False  # for signalling to stop running

    @staticmethod
    def init_port(serial_settings: SerialSettings) -> Union[serial.Serial, None]:
        try:
            port = serial.Serial(
                port=serial_settings.port,
                baudrate=serial_settings.baud_rate,
                parity=serial_settings.parity,
                stopbits=serial_settings.stop_bits,
                bytesize=serial_settings.bytesize
            )
            logging.info("Serial port connected")
            return port
        except serial.SerialException as e:
            logging.error(f"SerialException on initialization: {e}")

    def get_line(self) -> Union[bytes, None]:
        if self.port:
            try:
                line = self.port.readline()
                return line
            except serial.SerialException as e:
                logging.error(f"SerialException while reading: {e}; retrying...")
                self.port.close()
                self.port = self.init_port(self.serial_settings)
