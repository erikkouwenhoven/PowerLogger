from Application.plugin import Plugin, Publisher
from P1System.p1_interface import P1Interface, P1Sample
from DataHolder.data_holder import DataHolder
from DataHolder.data_item import DataItem
from Utils.settings import Settings


class P1Plugin(Plugin):

    plugin_name = "P1Plugin"
    outgoing_event = "P1SampleAcquired"
    react_to_events = ("StopSampling", )

    def __init__(self, publisher: Publisher, data_holder: DataHolder):
        super().__init__(self.plugin_name, publisher, self.react_to_events)
        self.data_holder = data_holder
        self.p1_interface = P1Interface(Settings().get_measurement_p1_signals(), self.post_sample_CB)

    def update(self, event_key, data):
        if event_key == self.react_to_events[0]:
            self.p1_interface.stop()

    def post_sample_CB(self, p1_sample: P1Sample):
        if p1_data_item := p1_sample.to_data_item(Settings().get_data_store_signals(Settings().get_P1_data_store())):
            self.data_holder.addMeasurement(Settings().get_P1_data_store(), p1_data_item)
        self.publisher.publish(self.outgoing_event, None)

    def start(self):
        self.p1_interface.start()
