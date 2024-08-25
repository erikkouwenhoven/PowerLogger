from Utils.settings import Settings
from Application.plugin import Publisher
from Application.Plugins.p1_plugin import P1Plugin
from Application.Plugins.sma_plugin import SMAPlugin
from Application.Plugins.zwave_plugin import ZWavePlugin
from Application.processor import Processor
from Application.inquirer import Inquirer
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
    - inquirer: answers to questions of external origin (i.e. web server)
    """

    def __init__(self):
        super().__init__()
        self.data_holder = DataHolder()
        P1Plugin(self, self.data_holder.data_store(Settings().get_P1_data_store()).data)
        SMAPlugin(self, self.data_holder.data_store(Settings().get_SMA_data_store()).data)
        ZWavePlugin(self, self.data_holder.data_store(Settings().get_ZWave_data_store()).data)

        self.processor = Processor(self.data_holder)
        self.inquirer = Inquirer(self.data_holder, self.get_plugins())
        self.webServer = ThreadedServer(self.processor)
        self.scheduler = Scheduler(self.processor)
        # NB in onderstaande regel blijft het proces eeuwig hangen, hierna geen acties meer doen dus
        getattr(self.get_plugin(P1Plugin.plugin_name), 'start')()
