from Application.Plugins.plugin import Plugin, Publisher
from P1System.p1_interface import P1Interface, P1Sample
from DataHolder.storage import Storage
from Utils.settings import Settings


class P1Plugin(Plugin):

    plugin_name = "P1Plugin"
    outgoing_event = "P1SampleAcquired"
    react_to_events = ("StopSampling", )

    def __init__(self, publisher: Publisher, data_storage: Storage):
        super().__init__(self.plugin_name, publisher, self.react_to_events)
        self.data_storage = data_storage
        self.p1_interface = P1Interface(Settings().get_measurement_p1_signals(), self.post_sample_cb)

    def update(self, event_key, data):
        if event_key == self.react_to_events[0]:
            self.p1_interface.stop()

    def post_sample_cb(self, p1_sample: P1Sample):
        if p1_data_item := p1_sample.to_data_item(self.p1_interface.reqValues):
            self.data_storage.add_measurement(p1_data_item)
        self.publisher.publish(self.outgoing_event, None)

    def start(self):
        self.p1_interface.start()
