from Application.plugin import Plugin, Publisher
from datetime import datetime
from SMASystem.sma_interface import SMAInterface, SMADataType
from DataHolder.data_item import DataItemSpec, DataItem
from Utils.settings import Settings


class SMAPlugin(Plugin):

    plugin_name = "SMAPlugin"
    react_to_events = ("P1SampleAcquired",)

    def __init__(self, publisher: Publisher, data_holder: DataHolder):
        super().__init__(self.plugin_name, publisher, self.react_to_events)
        self.data_holder = data_holder
        self.sma_interface = SMAInterface()

    def update(self, event_key, data):
        if event_key == self.react_to_events[0]:
            data_item = DataItem(DataItemSpec({SMADataType.SOLAR.name: SMAInterface.c_POWER_UNIT}),
                                 timestamp=datetime.timestamp(datetime.now()))
            data_item.set_value(SMADataType.SOLAR.name, self.sma_interface.getCurrentPower())
            self.data_holder.addMeasurement(Settings().get_SMA_data_store(), data_item)
