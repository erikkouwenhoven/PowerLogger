import serial
from dataclasses import dataclass
from Utils.settings import Settings


@dataclass
class SerialSettings:
    port: str = Settings().rs232Port()
    baudrate: int = Settings().rs232Baud()
    parity: str = eval(Settings().rs232Parity())
    stopbits: int = eval(Settings().rs232Stopbits())
    bytesize: int = eval(Settings().rs232Bytesize())
