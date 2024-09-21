from dataclasses import dataclass
from Utils.settings import Settings


@dataclass
class SerialSettings:
    port: str = Settings().rs232_port()
    baud_rate: int = Settings().rs232_baud()
    parity: str = Settings().rs232_parity()
    stop_bits: int = Settings().rs232_stopbits()
    bytesize: int = Settings().rs232_bytesize()
