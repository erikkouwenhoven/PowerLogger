from Application.processor import Processor
from P1System.p1_interface import P1Interface
from SMASystem.sma_interface import SMAInterface
from DataHolder.data_holder import DataHolder
from WebServer.threaded_server import ThreadedServer
from Scheduler.scheduler import Scheduler


class Controller:
    """
    There is only one controller, it is at the top of the hierarchy.
    It manages the following subsystems:
    - master measuring system running continuously once started
    - slave measuring system following the master's timing (controlled by the processor)
    - data holder holds collection of storages for time signals, volatile or persistent, circular or linear
    - web server receiving incoming requests
    - scheduler for management of scheduled activities
    - processor managing all signals and reaction on these subsequently
    """

    def __init__(self):
        self.p1_interface = P1Interface()
        self.sma_interface = SMAInterface()
        self.data_holder = DataHolder()
        self.processor = Processor(self.p1_interface, self.sma_interface, self.data_holder)
        self.webServer = ThreadedServer(self.processor)
        self.scheduler = Scheduler(self.processor)
        self.p1_interface.start(postSampleCB=self.processor.p1SampleAcquired)
