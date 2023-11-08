from typing import Optional
from P1System.data_classes import P1Sample
from P1System.interpreter import Interpreter
from P1System.serial_settings import SerialSettings
from P1System.data_classes import P1DataType


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

    def __init__(self, p1_value_types: list[P1DataType]):
        self.reqValues = P1DataType.all_poss() if p1_value_types is None else p1_value_types
        self.interpreter = Interpreter(SerialSettings())
        self.sample: Optional[P1Sample] = None
        self.interval = None
        self.postSampleCB = None

    def start(self, interval=None, postSampleCB=None):
        self.interval = interval
        self.interpreter.sync_sample()
        if postSampleCB:
            self.postSampleCB = postSampleCB
        self.interpreter.runContinuously(self.reqValues, self._sampleComplete)

    def singleShot(self):
        self.interpreter.sync_sample()
        sample = self.interpreter.get_sample(self.reqValues)
        return sample

    def stop(self):
        self.interpreter.stop_running()

    def getSample(self):
        return self.sample

    def get_raw_lines(self):
        return self.interpreter.get_raw_lines()

    def _sampleComplete(self, sample: P1Sample) -> None:
        self.sample = sample
        if self.postSampleCB:
            self.postSampleCB()

    def get_sampling_period(self):
        return self.interpreter.get_sampling_period()
