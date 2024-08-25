import logging
from Application.plugin import Plugin, Publisher
from ZWaveSystem.zwave_interface import ZWaveInterface
from DataHolder.storage import Storage
from DataHolder.data_item import DataItem
from Utils.settings import Settings


class ZWavePlugin(Plugin):

    plugin_name = "ZWavePlugin"
    react_to_events = tuple()

    def __init__(self, publisher: Publisher, data_storage: Storage):
        super().__init__(self.plugin_name, publisher, self.react_to_events)
        self.data_storage = data_storage
        self.zwave_interface = ZWaveInterface(self.post_sample_cb)
        self.zwave_interface.register(Settings().get_zwave_subscriptions())

    def update(self, event_key, data):
        pass

    def post_sample_cb(self, data_item: DataItem):
        logging.debug(f"zwaveSampleAcquired: {data_item}")
        self.data_storage.addMeasurement(data_item, no_zeros=True, min_time_spacing=Settings().get_min_storage_time_diff_seconds())
