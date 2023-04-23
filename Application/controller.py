from Application.processor import Processor
from P1System.p1_interface import P1Interface
from SMASystem.sma_interface import SMAInterface
from DataHolder.data_holder import DataHolder
from P1System.serial_settings import SerialSettings
from P1System.data_classes import DataType


class Controller:

    def __init__(self):
        self.p1_interface = P1Interface(SerialSettings(), DataType.all_poss())
        self.sma_interface = SMAInterface()
        self.data_holder = DataHolder()
        self.processor = Processor(self.p1_interface, self.sma_interface, self.data_holder)
        self.p1_interface.start(postSampleCB=self.processor.p1SampleAcquired)

