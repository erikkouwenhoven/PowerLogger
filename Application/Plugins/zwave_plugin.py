from Application.plugin import Plugin, Publisher
from ZWaveSystem.zwave_interface import ZWaveInterface


class ZWavePlugin(Plugin):

    plugin_name = "ZWavePlugin"
    react_to_events = ()

    def __init__(self, publisher: Publisher):
        super().__init__(self.plugin_name, publisher, self.react_to_events)
        self.zwave_interface = ZWaveInterface(self.post_sample_cb)

    def update(self, event_key, data):
        pass

    def post_sample_cb(self):
        self.zwave_interface.getCurrentPower()  # TODO data vasthouden
