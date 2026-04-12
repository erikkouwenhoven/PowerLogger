from collections.abc import Callable
from P1System.p1_data_classes import P1Sample
from P1System.interpreter import Interpreter
from P1System.serial_settings import SerialSettings
from P1System.p1_data_classes import P1DataType


class P1Interface:
    """
        P1Interface: Interface to the P1System for reading the serial P1-interface
            - values are always stored together with their sampling time stamp
            - user-defined callback after each sample addition
            - sampling is either one-shot or periodically
            - sampling interval and buffer size is user specified when doing periodical sampling

        Definitions:
            - AcquisitionMode:
                CONTINUOUS
                SINGLE_SHOT
            - P1ValueType:
                USAGE_TARIFF_1
                USAGE_TARIFF_2
                PRODUCTION_TARIFF_1
                PRODUCTION_TARIFF_2
                TARIFF
                CURRENT_USAGE
                CURRENT_PRODUCTION
                CUMULATIVE_GAS

        Methods:
            P1Reader(serialSettings, p1ValueTypes)
                serial_settings:    configuration of serial port
                p1ValueTypes:       list of P1ValueType

            start(interval=None, bufSize=24*3600/10, callback=None)
                interval:           interval time in seconds; if None the reader is continuously running and interval
                                        time is determined by device
                callback:           function that is called after each sample addition

            singleShot()

            stop()

            getSample():            returns latest sample
    """

    def __init__(self, p1_value_types: list[P1DataType], external_post_sample_cb: Callable[[P1Sample], None]):
        self.reqValues: list[P1DataType] = P1DataType.all_poss() if p1_value_types is None else p1_value_types
        self.external_post_sample_cb = external_post_sample_cb
        self.interpreter = Interpreter(SerialSettings())
        self.current_sample: P1Sample | None = None
        self.interval: float | None = None

    def start(self, interval: float | None = None):
        self.interval = interval
        self.interpreter.sync_sample()
        self.interpreter.run_continuously(self.reqValues, self._sample_complete)

    def single_shot(self) -> P1Sample:
        self.interpreter.sync_sample()
        sample = self.interpreter.get_sample(self.reqValues)
        return sample

    def stop(self):
        self.interpreter.stop_running()

    def get_current_sample(self) -> P1Sample:
        return self.current_sample

    def get_raw_lines(self) -> list[bytes]:
        return self.interpreter.get_raw_lines()

    def _sample_complete(self, sample: P1Sample) -> None:
        self.current_sample = sample
        if self.external_post_sample_cb:
            self.external_post_sample_cb(sample)

    def get_sampling_period(self) -> float | None:
        return self.interpreter.get_sampling_period()
