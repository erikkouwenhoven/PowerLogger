from Application.plugin import Publisher
from Application.Plugins.p1_plugin import P1Plugin
from Application.Plugins.sma_plugin import SMAPlugin
from Application.Plugins.zwave_plugin import ZWavePlugin
from Application.processor import Processor
from DataHolder.data_holder import DataHolder
from WebServer.threaded_server import ThreadedServer
from Scheduler.scheduler import Scheduler


class Application(Publisher):
    """
    The main application, it is at the top of the hierarchy. Inherits from Publisher.
    It manages the following subsystems:
    - data holder holds collection of storages for time signals, volatile or persistent, circular or linear
    - the plugins; these hold their data
    - web server receiving incoming requests
    - scheduler for management of scheduled activities
    - processor managing all signals and reaction on these subsequently
    """

    def __init__(self):
        super().__init__()
        self.data_holder = DataHolder()
        P1Plugin(self, self.data_holder)
        SMAPlugin(self, self.data_holder)
        ZWavePlugin(self, self.data_holder)

        self.processor = Processor(self.data_holder)
        self.webServer = ThreadedServer(self.processor)
        self.scheduler = Scheduler(self.processor)
        # NB in onderstaande regel blijft het proces eeuwig hangen, hierna geen acties meer doen dus
        self.get_plugin(P1Plugin.plugin_name).start()
