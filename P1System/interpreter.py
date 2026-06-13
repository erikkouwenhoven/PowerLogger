import logging
from collections.abc import Callable
from datetime import datetime
from P1System.crc16 import modbus_crc16
from P1System.p1_data_classes import P1DataType, P1Sample
from P1System.p1_data_classes import P1Value
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
        P1DataType.CUMULATIVE_GAS: b"0-1:24.2",
    }

    # startTelegram = b'XMX5LGBBFG1012622655'  # de oude meter
    startTelegram = b'KAIFA-METER'
    end_telegram = b'!'

    def __init__(self, serial_settings: SerialSettings):
        self.reader: SerialReader = SerialReader(serial_settings)
        self._stop_running: bool = False
        self._raw_lines: list[bytes] = []
        self.start_time: datetime | None = None
        self.num_samples: int | None = None
        self.sampling_period: float | None = None

    def sync_sample(self):
        line = self.reader.get_line()
        logging.debug(f"P1Plugin sync_sample, first line: {line}")
        while line and self.end_telegram not in line:
            line = self.reader.get_line()
            logging.debug(f"P1Plugin sync_sample, following line: {line}")
        if line:
            logging.debug(f"found end_telegram in line: {line}")
        else:
            logging.debug("no more lines")

    def get_sample(self, requested_values: list[P1DataType]) -> P1Sample | None:
        sample = P1Sample(requested_values)
        self._raw_lines.clear()
        while line := self.reader.get_line():
            self._raw_lines.append(line)
            if self.end_telegram in line:
                break
        if obtained_crc := self.get_crc(self._raw_lines):
            if obtained_crc != modbus_crc16(self.data_message(self._raw_lines)):
                data_message = self.data_message(self._raw_lines)
                logging.error(f"Invalid sample: crc received={hex(obtained_crc)} crc calced={hex(modbus_crc16(data_message))} {self._raw_lines}\n {data_message=}")
                return None
        else:
            logging.error("No CRC obtained")
        for line in self._raw_lines:
            if value := self.decode(line, requested_values):
                sample.add_value(value)
        return sample

    def data_message(self, raw_lines: list[bytes]) -> bytes:  # TODO static
        result = bytes(0)
        for line in raw_lines:
            if self.startTelegram in line:
                # logging.debug(f"data_message: start found in line {line}; split={line.split(b'/')[1]}")
                logging.debug(f"data_message: start found in line {line}")
                # alle '/'-karakters aan het begin vervangen door 1 '/'
                cnt = 0
                while line[cnt] == ord('/'):
                    cnt += 1
                logging.debug(f"eerste regel toevoegen aan data_message {line[cnt - 1:]}; {cnt=}")
                result += line[cnt - 1:]
                # result += b'/' +
            elif self.end_telegram in line:
                result += self.end_telegram
            elif len(result) > 0:  # pas regels overnemen als startTelegran is geweest
                result += line
        return result

    def get_crc(self, raw_lines: list[bytes]) -> int | None:
        for line in reversed(raw_lines):
            try:
                if line[0] == ord(self.end_telegram):
                    return int(line[1:5], 16)
            except (ValueError, IndexError):
                logging.error(f"get_crc: {line=}")
                return None
        logging.error(f"get_crc: no crc {raw_lines=}")
        return None

    def run_continuously(self, requested_values: list[P1DataType], post_sample_cb: Callable[[P1Sample], None] | None):
        logging.info(f"Start continuous sampling for values {requested_values}")
        self._stop_running = False
        self.start_time = datetime.now()
        self.num_samples = 0
        while not self._stop_running:
            if sample := self.get_sample(requested_values):
                self.num_samples += 1
                if post_sample_cb:
                    post_sample_cb(sample)

    def stop_running(self):
        self._stop_running = True

    def decode(self, line: bytes, requested_values: list[P1DataType]) -> P1Value | None:
        for req in requested_values:
            if req in self.obisCode:
                pos = line.find(self.obisCode[req])
                if pos != -1:
                    bracket_open = line.rfind(b'(', pos)  # Last occurrence, for gas
                    bracket_close = line.rfind(b')', pos)
                    if bracket_open != -1 and bracket_close != -1:
                        if p1_value := self.decode_value(req, line[bracket_open + 1:bracket_close], self.second_value(line, bracket_open)):
                            return p1_value
                        else:
                            print(f"decode: geen value toegekend {req=}, {line=}")
        return None

    @staticmethod
    def second_value(line: bytes, bracket_open: int) -> bytes | None:
        if (bracket_open_2 := line.find(b'(')) != bracket_open:
            bracket_close_2 = line.find(b')')
            return line[bracket_open_2 + 1:bracket_close_2]
        return None

    @staticmethod
    def decode_value(datatype: P1DataType, encoded_str: bytes, extra: bytes | None) -> P1Value | None:
        ret_val = P1Value(datatype)
        if datatype == P1DataType.TIMESTAMP:
            ret_val.set_timestamp(encoded_str)
        else:
            if (split := encoded_str.find(b'*')) != -1:
                try:
                    value = float(encoded_str[:split])
                except ValueError:  # in some rare cases the string contains weird characters
                    logging.error(f"decodeValue: could not convert {encoded_str.decode()} to float; {datatype=}, {encoded_str=}, {extra=}")
                    return None
                unit = encoded_str[split + 1:]
                # even voor de debug
                # if unit not in ('kW', 'kWh'):
                #     logging.critical(f"PANIC found unit {unit} in {encoded_str}")
                ret_val.set_value(value, unit=unit)
            else:
                try:
                    value = int(encoded_str)
                except ValueError:  # in some rare cases the string contains weird characters
                    logging.error(f"decodeValue: could not convert {encoded_str.decode()} to int")
                    return None
                ret_val.set_value(value, unit=None)
        if extra:
            ret_val.set_extra_timestamp(extra)
        return ret_val

    def get_raw_lines(self) -> list[bytes]:
        return self._raw_lines

    def get_sampling_period(self, update: bool = False) -> float | None:
        if self.sampling_period is None or update is True:
            if self.num_samples and self.start_time:
                self.sampling_period = (datetime.now() - self.start_time).total_seconds() / self.num_samples
        return self.sampling_period
