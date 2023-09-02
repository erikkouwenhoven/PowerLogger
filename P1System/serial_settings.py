from dataclasses import dataclass
from Utils.settings import Settings


@dataclass
class SerialSettings:
    port: str = Settings().rs232Port()
    baudrate: int = Settings().rs232Baud()
    parity: str = Settings().rs232Parity()
    stopbits: int = Settings().rs232Stopbits()
    bytesize: int = Settings().rs232Bytesize()
