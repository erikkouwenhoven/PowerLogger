import logging
from datetime import datetime
from Application.plugin import Plugin, Publisher
from ZWaveSystem.zwave_interface import ZWaveInterface
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from DataHolder.storage import Storage
from DataHolder.data_item import DataItemSpec, DataItem
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

    def post_sample_cb(self, z_wave_node: ZWaveNode, z_wave_value: ZWaveValue):
        data_item = self.zwave_to_data_item(z_wave_node, z_wave_value)
        logging.debug(f"zwaveSampleAcquired: {data_item}")
        self.data_storage.addMeasurement(data_item, no_zeros=True, min_time_spacing=Settings().get_min_storage_time_diff_seconds())

    def zwave_to_data_item(self, z_wave_node: ZWaveNode, z_wave_value: ZWaveValue) -> DataItem:
        zwave_signal_name = self.zwave_interface.zwave_signal_name(z_wave_node, z_wave_value)
        data_item = DataItem(DataItemSpec({zwave_signal_name: z_wave_value.units}),
                             timestamp=datetime.timestamp(datetime.now()))
        data_item.set_value(zwave_signal_name, z_wave_value.data)
        return data_item
