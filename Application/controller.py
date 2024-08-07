from Utils.settings import Settings
from Application.processor import Processor
from P1System.p1_interface import P1Interface
from SMASystem.sma_interface import SMAInterface
from ZWaveSystem.zwave_interface import ZWaveInterface
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
        self.p1_interface = P1Interface(Settings().get_measurement_p1_signals())
        self.sma_interface = SMAInterface()
        self.zwave_interface = ZWaveInterface()
        self.data_holder = DataHolder()
        self.processor = Processor(self.p1_interface, self.sma_interface, self.zwave_interface, self.data_holder)
        self.zwave_interface.register(Settings().get_zwave_subscriptions(), post_sample_CB=self.processor.zwaveSampleAcquired)
        self.webServer = ThreadedServer(self.processor)
        self.scheduler = Scheduler(self.processor)
        # NB in onderstaande regel blijft het proces eeuwig hangen, hierna geen acties meer doen dus
        self.p1_interface.start(post_sample_CB=self.processor.p1SampleAcquired)
