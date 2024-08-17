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
        self.filter_and_differentiate(p1_sample)
        self.publisher.publish(self.outgoing_event, None)

    def filter_and_differentiate(self, p1_sample: P1Sample):
        if data_item := p1_sample.extra_signal_to_data_item(Settings().get_differential_source_signal()):
            data_store = self.data_holder.data_store(Settings().get_filtered_data_store())
            if data_store.data.last_time() != data_item.get_timestamp():
                data_store.data.append(data_item)
                self.data_holder.addMeasurement(Settings().get_filtered_data_store(), data_item)
                if prev_item := data_store.data.get_data_item(data_store.data.last_index(offset=1)):
                    delta = (data_item.get_value(Settings().get_differential_source_signal()) -
                             prev_item.get_value(Settings().get_differential_source_signal()))
                    data_item_spec = self.data_holder.data_store(
                        Settings().get_differential_dest_data_store()).data.data_item_spec
                    data_item_spec.set_unit(Settings().get_differential_dest_signal(),
                                            Settings().get_differential_dest_unit())
                    delta_data_item = DataItem(data_item_spec, timestamp=prev_item.get_timestamp())
                    delta_data_item.set_value(Settings().get_differential_dest_signal(), delta)
                    self.data_holder.addMeasurement(Settings().get_differential_dest_data_store(), delta_data_item)

    def start(self):
        self.p1_interface.start()
