import logging
from P1System.data_classes import DataType, P1Sample
from P1System.data_classes import P1Value
from P1System.serial_reader import SerialReader


class Interpreter:
    """
    Interpret raw string obtained from P1 slimme meter
    Refer to https://www.netbeheernederland.nl/_upload/Files/Slimme_meter_15_a727fce1f1.pdf

    Methods:
        sync_sample
        get_sample
    """

    obisCode = {
        DataType.TIMESTAMP: b"0-0:1.0.0",
        DataType.USAGE_TARIFF_1: b"1-0:1.8.1",
        DataType.USAGE_TARIFF_2: b"1-0:1.8.2",
        DataType.PRODUCTION_TARIFF_1: b"1-0:2.8.1",
        DataType.PRODUCTION_TARIFF_2: b"1-0:2.8.2",
        DataType.TARIFF: b"0-0:96.14.0",
        DataType.CURRENT_USAGE: b"1-0:1.7.0",
        DataType.CURRENT_PRODUCTION: b"1-0:2.7.0",
        DataType.CURRENT_USAGE_PHASE1: b"1-0:21.7.0",
        DataType.CURRENT_USAGE_PHASE2: b"1-0:41.7.0",
        DataType.CURRENT_USAGE_PHASE3: b"1-0:61.7.0",
        DataType.CURRENT_PRODUCTION_PHASE1: b"1-0:22.7.0",
        DataType.CURRENT_PRODUCTION_PHASE2: b"1-0:42.7.0",
        DataType.CURRENT_PRODUCTION_PHASE3: b"1-0:62.7.0",
        DataType.USAGE_GAS: b"0-1:24.2",  # TODO levert twee waarden, tijd en kuub
    }

    startTelegram = b'XMX5LGBBFG1012622655'

    def __init__(self, serial_settings):
        self.reader: SerialReader = SerialReader(serial_settings)
        self.stop_running = False
        self.rawLines = []

    def sync_sample(self):
        line = self.reader.getLine()
        while line and self.startTelegram not in line:
            line = self.reader.getLine()

    def get_sample(self, requestedValues):
        sample = P1Sample(requestedValues)
        line = self.reader.getLine()
        self.rawLines.clear()
        while line and self.startTelegram not in line:
            self.rawLines.append(line)
            reset, value = self.decode(line, requestedValues)
            assert reset is False
            if value:
                sample.addValue(value)
            line = self.reader.getLine()
        return sample

    def runContinuously(self, requestedValues, postSampleCB):
        logging.info(f"Start continuous sampling for values {requestedValues}")
        self.stop_running = False
        while self.stop_running is False:
            sample = self.get_sample(requestedValues)
            if postSampleCB:
                postSampleCB(sample)

    def decode(self, line, requestedValues):
        if self.startTelegram in line:
            return True, None
        else:
            reset = False
#        print("Decode request for line {}".format(line))
#        print(f"obisCode: {self.obisCode}")
        for req in requestedValues:
#            print("processing request {} i.e. {}".format(req, self.obisCode[req]))
            if req in self.obisCode:
                pos = line.find(self.obisCode[req])
                if pos != -1:
    #                print(f"Found {req} at pos {pos}")
                    bracketOpen = line.rfind(b'(', pos)  # Last occurence, for gas
                    bracketClose = line.rfind(b')', pos)
    #                print("haakje open {} haakje dicht {}".format(bracketOpen, bracketClose))
                    if bracketOpen != -1 and bracketClose != -1:
                        value = self.decodeValue(req, line[bracketOpen+1:bracketClose])
                        if value:
                            return reset, value
        return False, None

    def decodeValue(self, dataType, encodedStr):
        retVal = P1Value(dataType)
        split = encodedStr.find(b'*')
        if split != -1:
            try:
                value = float(encodedStr[:split])
            except ValueError:  # in some rare cases the string contains weird characters
                value = None
                logging.error(f"decodeValue: could not convert {encodedStr} to float")
            unit = encodedStr[split+1:]
            retVal.setValue(value, unit=unit)
        else:
            retVal.setValue(encodedStr)
        return retVal

    def getRawLines(self):
        return self.rawLines
