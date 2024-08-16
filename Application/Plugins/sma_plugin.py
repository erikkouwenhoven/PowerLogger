from Application.plugin import Plugin, Publisher
from SMASystem.sma_interface import SMAInterface


class SMAPlugin(Plugin):

    plugin_name = "SMAPlugin"
    react_to_events = ("P1SampleAcquired",)

    def __init__(self, publisher: Publisher):
        super().__init__(self.plugin_name, publisher, self.react_to_events)
        self.sma_interface = SMAInterface()

    def update(self, event_key, data):
        if event_key == self.react_to_events[0]:
            self.sma_interface.getCurrentPower()  # TODO data vasthouden
