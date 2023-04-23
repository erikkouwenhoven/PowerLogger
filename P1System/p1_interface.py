from P1System.interpreter import Interpreter


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
                USAGE_GAS

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

    def __init__(self, serial_settings, p1ValueTypes):
        self.reqValues = p1ValueTypes
        self.interpreter = Interpreter(serial_settings)
        self.sample = None
        self.interval = None
        self.postSampleCB = None

    def start(self, interval=None, postSampleCB=None):
        self.interval = interval
        self.interpreter.sync_sample()
        if postSampleCB:
            self.postSampleCB = postSampleCB
        self.interpreter.runContinuously(self.reqValues, self.sampleComplete)

    def singleShot(self):
        self.interpreter.sync_sample()
        sample = self.interpreter.get_sample(self.reqValues)
        return sample

    def stop(self):
        self.interpreter.stop_running()

    def sampleComplete(self, sample):
        self.sample = sample
        if self.postSampleCB:
            self.postSampleCB()

    def getSample(self):
        return self.sample

    def getRawLines(self):
        return self.interpreter.getRawLines()
