from Application.plugin import Plugin, Publisher
from datetime import datetime
from SMASystem.sma_interface import SMAInterface, SMADataType
from DataHolder.storage import Storage
from DataHolder.data_item import DataItemSpec, DataItem


class SMAPlugin(Plugin):

    plugin_name = "SMAPlugin"
    react_to_events = ("P1SampleAcquired",)

    def __init__(self, publisher: Publisher, data_storage: Storage):
        super().__init__(self.plugin_name, publisher, self.react_to_events)
        self.data_storage = data_storage
        self.sma_interface = SMAInterface()

    def update(self, event_key, data):
        if event_key == self.react_to_events[0]:
            data_item = DataItem(DataItemSpec({SMADataType.SOLAR.name: SMAInterface.c_POWER_UNIT}),
                                 timestamp=datetime.timestamp(datetime.now()))
            data_item.set_value(SMADataType.SOLAR.name, self.sma_interface.getCurrentPower())
            self.data_storage.addMeasurement(data_item)
