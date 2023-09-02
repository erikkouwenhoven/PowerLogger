import logging
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
        P1DataType.USAGE_GAS: b"0-1:24.2",  # TODO levert twee waarden, tijd en kuub
    }

    startTelegram = b'XMX5LGBBFG1012622655'

    def __init__(self, serial_settings: SerialSettings):
        self.reader: SerialReader = SerialReader(serial_settings)
        self.stop_running = False
        self.rawLines = []

    def sync_sample(self):
        line = self.reader.getLine()
        while line and self.startTelegram not in line:
            line = self.reader.getLine()

    def get_sample(self, requested_values) -> P1Sample:
        sample = P1Sample(requested_values)
        line = self.reader.getLine()
        self.rawLines.clear()
        while line and self.startTelegram not in line:
            self.rawLines.append(line)
            reset, value = self.decode(line, requested_values)
            assert reset is False
            if value:
                sample.addValue(value)
            line = self.reader.getLine()
        return sample

    def runContinuously(self, requested_values: list[str], post_sample_cb: classmethod):
        logging.info(f"Start continuous sampling for values {requested_values}")
        self.stop_running = False
        while self.stop_running is False:
            sample = self.get_sample(requested_values)
            if post_sample_cb:
                post_sample_cb(sample)

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
                    bracketOpen = line.rfind(b'(', pos)  # Last occurence, for gas
                    bracketClose = line.rfind(b')', pos)
    #                print("haakje open {} haakje dicht {}".format(bracketOpen, bracketClose))
                    if bracketOpen != -1 and bracketClose != -1:
                        value = self.decode_value(req, line[bracketOpen + 1:bracketClose])
                        if value:
                            return reset, value
        return False, None

    @staticmethod
    def decode_value(datatype, encoded_str):
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
        return retVal

    def getRawLines(self):
        return self.rawLines
