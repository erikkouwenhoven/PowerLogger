import logging
from Application.plugin import Plugin, Publisher
from ZWaveSystem.zwave_interface import ZWaveInterface
from ZWaveSystem.data_classes import SampleZWave
from DataHolder.data_holder import DataHolder
from Utils.settings import Settings


class ZWavePlugin(Plugin):

    plugin_name = "ZWavePlugin"
    react_to_events = tuple()

    def __init__(self, publisher: Publisher, data_holder: DataHolder):
        super().__init__(self.plugin_name, publisher, self.react_to_events)
        self.data_holder = data_holder
        self.zwave_interface = ZWaveInterface(self.post_sample_cb)
        self.zwave_interface.register(Settings().get_zwave_subscriptions())

    def update(self, event_key, data):
        pass

    def post_sample_cb(self, zwave_sample: SampleZWave):
        logging.debug(f"zwaveSampleAcquired: {zwave_sample}")
        if data_item := zwave_sample.to_data_item(zwave_sample.get_data_types()):
            data_store = Settings().get_ZWave_data_store(zwave_sample.node_id, zwave_sample.get_data_types())
            self.data_holder.addMeasurement(data_store, data_item, no_zeros=True, min_time_spacing=Settings().get_min_storage_time_diff_seconds())
