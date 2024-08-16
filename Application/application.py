from Utils.settings import Settings
from Application.plugin import Publisher
from Application.Plugins.p1_plugin import P1Plugin
from Application.Plugins.sma_plugin import SMAPlugin
from Application.Plugins.zwave_plugin import ZWavePlugin
from Application.processor import Processor
from P1System.p1_interface import P1Interface
from SMASystem.sma_interface import SMAInterface
from ZWaveSystem.zwave_interface import ZWaveInterface
from DataHolder.data_holder import DataHolder
from WebServer.threaded_server import ThreadedServer
from Scheduler.scheduler import Scheduler


class Application(Publisher):
    """
    The main application, it is at the top of the hierarchy. Inherits from Publisher.
    It manages the following subsystems:
    - the plugins; these hold their in-memory data
    - data holder holds collection of storages for time signals, volatile or persistent, circular or linear
    - web server receiving incoming requests
    - scheduler for management of scheduled activities
    - processor managing all signals and reaction on these subsequently
    """

    def __init__(self):
        super().__init__()
        P1Plugin(self)
        SMAPlugin(self)
        ZWavePlugin(self)

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
