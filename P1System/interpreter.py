import logging
from datetime import datetime
from typing import Optional, Callable
from P1System.data_classes import P1DataType, P1Sample
from P1System.data_classes import P1Value
from P1System.serial_reader import SerialReader
from P1System.serial_settings import SerialSettings


class Interpreter:
    """
    Interpret raw string obtained from P1 slimme meter
    Refer to https://www.netbeheernederland.nl/_upload/Files/Slimme_meter_15_a727fce1f1.pdf

    Methods:
        sync_sample
        get_sample
    """

    obisCode = {
        P1DataType.TIMESTAMP: b"0-0:1.0.0",
        P1DataType.USAGE_TARIFF_1: b"1-0:1.8.1",
        P1DataType.USAGE_TARIFF_2: b"1-0:1.8.2",
        P1DataType.PRODUCTION_TARIFF_1: b"1-0:2.8.1",
        P1DataType.PRODUCTION_TARIFF_2: b"1-0:2.8.2",
        P1DataType.TARIFF: b"0-0:96.14.0",
        P1DataType.CURRENT_USAGE: b"1-0:1.7.0",
        P1DataType.CURRENT_PRODUCTION: b"1-0:2.7.0",
        P1DataType.CURRENT_USAGE_PHASE1: b"1-0:21.7.0",
        P1DataType.CURRENT_USAGE_PHASE2: b"1-0:41.7.0",
        P1DataType.CURRENT_USAGE_PHASE3: b"1-0:61.7.0",
        P1DataType.CURRENT_PRODUCTION_PHASE1: b"1-0:22.7.0",
        P1DataType.CURRENT_PRODUCTION_PHASE2: b"1-0:42.7.0",
        P1DataType.CURRENT_PRODUCTION_PHASE3: b"1-0:62.7.0",
        P1DataType.CUMULATIVE_GAS: b"0-1:24.2",  # TODO levert twee waarden, tijd en kuub
    }

    startTelegram = b'XMX5LGBBFG1012622655'

    def __init__(self, serial_settings: SerialSettings):
        self.reader: SerialReader = SerialReader(serial_settings)
        self._stop_running: bool = False
        self._raw_lines: list[str] = []
        self.start_time: Optional[datetime] = None
        self.num_samples: Optional[int] = None
        self.sampling_period: Optional[float] = None

    def sync_sample(self):
        line = self.reader.getLine()
        while line and self.startTelegram not in line:
            line = self.reader.getLine()

    def get_sample(self, requested_values) -> P1Sample:
        sample = P1Sample(requested_values)
        line = self.reader.getLine()
        self._raw_lines.clear()
        while line and self.startTelegram not in line:
            self._raw_lines.append(line)
            reset, value = self.decode(line, requested_values)
            assert reset is False
            if value:
                sample.addValue(value)
            line = self.reader.getLine()
        return sample

    def runContinuously(self, requested_values: list[str], post_sample_cb: Callable[[P1Sample], None]):
        logging.info(f"Start continuous sampling for values {requested_values}")
        self._stop_running = False
        self.start_time = datetime.now()
        self.num_samples = 0
        while self._stop_running is False:
            sample = self.get_sample(requested_values)
            self.num_samples += 1
            if post_sample_cb:
                post_sample_cb(sample)

    def stop_running(self):
        self._stop_running = True

    def decode(self, line: bytes, requested_values: list[str]) -> (bool, float):
        if self.startTelegram in line:
            return True, None
        else:
            reset = False
#        print("Decode request for line {}".format(line))
#        print(f"obisCode: {self.obisCode}")
        for req in requested_values:
#            print("processing request {} i.e. {}".format(req, self.obisCode[req]))
            if req in self.obisCode:
                pos = line.find(self.obisCode[req])
                if pos != -1:
    #                print(f"Found {req} at pos {pos}")
                    bracketOpen = line.rfind(b'(', pos)  # Last occurrence, for gas
                    bracketClose = line.rfind(b')', pos)
    #                print("haakje open {} haakje dicht {}".format(bracketOpen, bracketClose))
                    if bracketOpen != -1 and bracketClose != -1:
                        value = self.decode_value(req, line[bracketOpen + 1:bracketClose], self.second_value(line, bracketOpen))
                        if value:
                            return reset, value
        return False, None

    @staticmethod
    def second_value(line: bytes, bracketOpen: int):
        if (bracketOpen_2 := line.find(b'(')) != bracketOpen:
            bracketClose_2 = line.find(b')')
            return line[bracketOpen_2 + 1:bracketClose_2]

    @staticmethod
    def decode_value(datatype, encoded_str, extra):
        retVal = P1Value(datatype)
        split = encoded_str.find(b'*')
        if split != -1:
            try:
                value = float(encoded_str[:split])
            except ValueError:  # in some rare cases the string contains weird characters
                value = None
                logging.error(f"decodeValue: could not convert {encoded_str} to float")
            unit = encoded_str[split + 1:]
            retVal.setValue(value, unit=unit)
        else:
            retVal.setValue(encoded_str)
        if extra:
            retVal.set_extra_timestamp(extra)
        return retVal

    def get_raw_lines(self):
        return self._raw_lines

    def get_sampling_period(self, update: bool = False) -> float:
        if self.sampling_period is None or update is True:
            self.sampling_period = (datetime.now() - self.start_time).total_seconds() / self.num_samples
        return self.sampling_period
